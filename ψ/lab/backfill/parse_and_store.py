#!/usr/bin/env python3
"""Parse Discord fetch_messages output and store in SQLite + FTS5 + JSONL.

Usage:
    python parse_and_store.py <input_file>
    cat messages.txt | python parse_and_store.py

Stores to backfill.db (same dir), exports messages.jsonl, and prints
TF-IDF timeline analysis per day.
"""
import re
import sys
import os
import json
import sqlite3
import math
from collections import Counter, defaultdict
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "backfill.db")
JSONL_PATH = os.path.join(SCRIPT_DIR, "messages.jsonl")

# Default channel_id when parsing from text dump (not available in the format)
DEFAULT_CHANNEL_ID = "1512079809021214730"

# Regex: [TIMESTAMP] USERNAME: CONTENT  (id: MSG_ID) or (id: MSG_ID +Natt)
LINE_RE = re.compile(
    r'^\[(?P<timestamp>[^\]]+)\]\s+'
    r'(?P<username>[^:]+?):\s+'
    r'(?P<content>.*?)\s+'
    r'\(id:\s+(?P<msg_id>\d+)'
    r'(?:\s+\+(?P<att_count>\d+)att)?'
    r'\)\s*$'
)


def parse_line(line: str):
    """Parse a single line from the fetch_messages output."""
    line = line.rstrip('\n').rstrip('\r')
    m = LINE_RE.match(line)
    if not m:
        return None
    att = int(m.group('att_count')) if m.group('att_count') else 0
    # Replace ⏎ with actual newlines in content for readability
    content = m.group('content').replace(' ⏎ ', '\n').replace('⏎ ', '\n').replace(' ⏎', '\n')
    return {
        'timestamp': m.group('timestamp'),
        'username': m.group('username').strip(),
        'content': content,
        'message_id': m.group('msg_id'),
        'attachment_count': att,
        'has_attachments': 1 if att > 0 else 0,
    }


def init_db(db: sqlite3.Connection):
    """Create tables if not exist."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            author_name TEXT,
            content TEXT,
            timestamp TEXT NOT NULL,
            has_attachments INTEGER DEFAULT 0,
            indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_id);
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
    """)
    # FTS5 virtual table (standalone, not content-synced)
    try:
        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
            USING fts5(content, author_name)
        """)
    except sqlite3.OperationalError:
        pass


def store_messages(db, records, channel_id):
    """Insert parsed records into SQLite."""
    inserted = 0
    for rec in records:
        try:
            db.execute(
                "INSERT OR IGNORE INTO messages (id, channel_id, author_name, content, timestamp, has_attachments) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rec['message_id'], channel_id, rec['username'], rec['content'],
                 rec['timestamp'], rec['has_attachments'])
            )
            if db.total_changes:
                inserted += 1
        except sqlite3.IntegrityError:
            pass
    db.commit()
    # Rebuild FTS
    try:
        db.execute("DELETE FROM messages_fts")
        db.execute("INSERT INTO messages_fts(content, author_name) "
                   "SELECT content, author_name FROM messages")
        db.commit()
    except sqlite3.OperationalError as e:
        print(f"  [WARN] FTS rebuild failed: {e}")
        pass
    return inserted


def write_jsonl(records, path):
    """Write records as JSONL."""
    with open(path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')


# --- TF-IDF Analysis ---

# Thai and English stop words
STOP_WORDS = {
    # English
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall', 'must', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
    'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than', 'too',
    'very', 'just', 'because', 'if', 'when', 'where', 'how', 'what',
    'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'it', 'its',
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his',
    'she', 'her', 'they', 'them', 'their', 'up', 'out', 'about', 'then',
    'here', 'there', 'also', 'after', 'before',
    # Thai common particles/connectors
    'ที่', 'ของ', 'และ', 'ใน', 'เป็น', 'ได้', 'ไม่', 'มี', 'จะ', 'ว่า',
    'ให้', 'กับ', 'แล้ว', 'คือ', 'นี้', 'ก็', 'แต่', 'อยู่', 'ไป', 'มา',
    'ถ้า', 'จาก', 'ยัง', 'กัน', 'ทำ', 'หรือ', 'เรา', 'ผม', 'ครับ', 'ค่ะ',
    'นะ', 'ดี', 'เลย', 'ตอน', 'แบบ', 'อัน', 'เอา', 'ไหม', 'คะ',
    # Noise from Discord formatting
    'http', 'https', 'com', 'github', 'io', 'www', 'discord',
}

TOKEN_RE = re.compile(r'[a-zA-Z฀-๿]{2,}')


def tokenize(text: str) -> list[str]:
    """Simple tokenizer for mixed Thai/English text."""
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def compute_tfidf(docs_by_day):
    """Compute TF-IDF where each day is a document.

    Returns top 5 distinctive terms per day.
    """
    days = sorted(docs_by_day.keys())
    n_docs = len(days)
    if n_docs == 0:
        return {}

    # Document frequency
    df = Counter()
    tf_per_day = {}
    for day in days:
        tokens = docs_by_day[day]
        tf = Counter(tokens)
        tf_per_day[day] = tf
        for term in set(tokens):
            df[term] += 1

    result = {}
    for day in days:
        tf = tf_per_day[day]
        total_tokens = sum(tf.values()) or 1
        scores = {}
        for term, count in tf.items():
            # TF: normalized frequency
            tf_val = count / total_tokens
            # IDF: log(N / df)
            idf_val = math.log(n_docs / df[term]) if df[term] > 0 else 0
            scores[term] = tf_val * idf_val
        # Top 5 by TF-IDF score (must have score > 0 = distinctive)
        top = sorted(scores.items(), key=lambda x: -x[1])[:5]
        result[day] = [(term, round(score, 4)) for term, score in top if score > 0]

    return result


def print_stats(records, db):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("  PARSE & STORE STATS")
    print("=" * 60)

    # From parsed records
    usernames = set(r['username'] for r in records)
    dates = set(r['timestamp'][:10] for r in records)
    att_count = sum(r['attachment_count'] for r in records)
    msgs_with_att = sum(1 for r in records if r['has_attachments'])

    print(f"  Parsed lines:       {len(records)}")
    print(f"  Unique authors:     {len(usernames)}")
    print(f"  Date range:         {min(dates)} -> {max(dates)}")
    print(f"  Messages w/ attach: {msgs_with_att} ({att_count} total attachments)")
    print(f"  Authors:            {', '.join(sorted(usernames))}")

    # From DB
    db_count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    fts_count = 0
    try:
        fts_count = db.execute("SELECT COUNT(*) FROM messages_fts").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    print(f"\n  DB total messages:  {db_count}")
    print(f"  FTS indexed:        {fts_count}")
    print(f"  JSONL written to:   {JSONL_PATH}")
    print(f"  DB path:            {DB_PATH}")

    # Messages per author
    print("\n  Messages per author:")
    author_counts = Counter(r['username'] for r in records)
    for author, count in author_counts.most_common():
        print(f"    {author:30s} {count:3d}")


def print_tfidf_by_author(records):
    """TF-IDF where each author is a document -- find distinctive terms per author."""
    docs_by_author = defaultdict(list)
    for rec in records:
        tokens = tokenize(rec['content'])
        docs_by_author[rec['username']].extend(tokens)

    tfidf = compute_tfidf(dict(docs_by_author))

    print("\n" + "=" * 60)
    print("  TF-IDF BY AUTHOR (top 5 distinctive terms per author)")
    print("=" * 60)
    for author in sorted(tfidf.keys()):
        terms = tfidf[author]
        msg_count = sum(1 for r in records if r['username'] == author)
        if terms:
            term_str = ' | '.join(f"{t} ({s:.3f})" for t, s in terms)
            print(f"\n  {author}  [{msg_count} msgs]")
            print(f"    {term_str}")


def print_tfidf_by_hour(records):
    """TF-IDF where each hour block is a document."""
    docs_by_hour = defaultdict(list)
    for rec in records:
        hour = rec['timestamp'][:13]  # YYYY-MM-DDTHH
        tokens = tokenize(rec['content'])
        docs_by_hour[hour].extend(tokens)

    tfidf = compute_tfidf(dict(docs_by_hour))

    print("\n" + "=" * 60)
    print("  TF-IDF BY HOUR (top 5 distinctive terms per hour)")
    print("=" * 60)
    for hour in sorted(tfidf.keys()):
        terms = tfidf[hour]
        msg_count = sum(1 for r in records if r['timestamp'][:13] == hour)
        if terms:
            term_str = ' | '.join(f"{t} ({s:.3f})" for t, s in terms)
            print(f"\n  {hour}:00Z  [{msg_count} msgs]")
            print(f"    {term_str}")


def print_tfidf_timeline(records):
    """Group messages by date, compute TF-IDF, print timeline."""
    docs_by_day = defaultdict(list)
    for rec in records:
        day = rec['timestamp'][:10]
        tokens = tokenize(rec['content'])
        docs_by_day[day].extend(tokens)

    tfidf = compute_tfidf(dict(docs_by_day))

    print("\n" + "=" * 60)
    print("  TF-IDF TIMELINE (top 5 distinctive terms per day)")
    print("=" * 60)
    for day in sorted(tfidf.keys()):
        terms = tfidf[day]
        msg_count = sum(1 for r in records if r['timestamp'][:10] == day)
        term_str = ' | '.join(f"{t} ({s:.3f})" for t, s in terms) if terms else "(no distinctive terms)"
        print(f"\n  {day}  [{msg_count} msgs]")
        print(f"    {term_str}")


def main():
    # Read input
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    if not lines:
        print("No input. Usage: python parse_and_store.py <file> or pipe to stdin")
        sys.exit(1)

    # Parse
    records = []
    failed = 0
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        # Strip leading line number + tab if present (from cat -n output)
        stripped = re.sub(r'^\d+\t', '', line)
        rec = parse_line(stripped)
        if rec:
            records.append(rec)
        else:
            failed += 1
            if failed <= 5:
                print(f"  [WARN] Could not parse line {i}: {stripped[:80]}...")

    print(f"Parsed {len(records)} messages ({failed} failed)")

    if not records:
        print("No records parsed. Exiting.")
        sys.exit(1)

    # Store in SQLite
    db = sqlite3.connect(DB_PATH)
    init_db(db)
    inserted = store_messages(db, records, DEFAULT_CHANNEL_ID)
    print(f"Stored {inserted} new messages in SQLite")

    # Write JSONL
    write_jsonl(records, JSONL_PATH)
    print(f"Wrote {len(records)} records to {JSONL_PATH}")

    # Stats
    print_stats(records, db)

    # TF-IDF timeline
    print_tfidf_timeline(records)

    # TF-IDF by author (distinctive terms per person)
    print_tfidf_by_author(records)

    # TF-IDF by hour (useful when all data is same day)
    print_tfidf_by_hour(records)

    db.close()


if __name__ == "__main__":
    main()

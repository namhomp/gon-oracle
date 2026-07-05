#!/usr/bin/env python3
"""Gon Discord Mirror — paginated backfill from raw text dumps.
Reads Discord plugin fetch_messages output, stores in SQLite + FTS5.
Supports incremental: re-run with new dumps, dedupes by message_id.
"""
import sqlite3
import re
import json
import sys
import os
import math
from collections import Counter, defaultdict
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "backfill.db")

LINE_RE = re.compile(
    r'^\[(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\]\s+'
    r'(.+?):\s+'
    r'(.*?)\s*'
    r'\(id:\s*(\d+)(?:\s*\+(\d+)att)?\)\s*$',
    re.DOTALL
)

def init_db(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL DEFAULT '',
            author_name TEXT,
            content TEXT,
            timestamp TEXT NOT NULL,
            has_attachments INTEGER DEFAULT 0,
            attachment_count INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_msg_ts ON messages(timestamp);
        CREATE INDEX IF NOT EXISTS idx_msg_author ON messages(author_name);
    """)
    try:
        db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                      USING fts5(content, author_name)""")
    except sqlite3.OperationalError:
        pass

def parse_file(filepath, channel_id=""):
    messages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line = line.replace(' ⏎ ', '\n')
            m = LINE_RE.match(line)
            if m:
                ts, author, content, msg_id, att_count = m.groups()
                messages.append({
                    'id': msg_id,
                    'channel_id': channel_id,
                    'author_name': author.strip(),
                    'content': content.strip(),
                    'timestamp': ts,
                    'has_attachments': 1 if att_count else 0,
                    'attachment_count': int(att_count) if att_count else 0,
                })
    return messages

def store_messages(db, messages):
    new = 0
    for msg in messages:
        try:
            db.execute(
                "INSERT OR IGNORE INTO messages (id, channel_id, author_name, content, timestamp, has_attachments, attachment_count) VALUES (?,?,?,?,?,?,?)",
                (msg['id'], msg['channel_id'], msg['author_name'], msg['content'], msg['timestamp'], msg['has_attachments'], msg['attachment_count'])
            )
            if db.total_changes:
                new += 1
        except sqlite3.IntegrityError:
            pass
    db.commit()
    return new

def rebuild_fts(db):
    db.execute("DELETE FROM messages_fts")
    db.execute("INSERT INTO messages_fts(rowid, content, author_name) SELECT rowid, content, author_name FROM messages")
    db.commit()

def tfidf_by_day(db):
    rows = db.execute("SELECT substr(timestamp, 1, 10) as day, content FROM messages ORDER BY day").fetchall()
    docs = defaultdict(list)
    for day, content in rows:
        docs[day].append(content)

    stop_words = {'ครับ','ค่ะ','ที่','ไม่','ได้','ให้','จาก','เป็น','มี','อยู่','ใน','แล้ว',
                  'นี้','ว่า','กับ','จะ','ทำ','คือ','the','to','and','is','of','a','in','for',
                  'it','on','that','this','with','are','was','be','as','at','or','an','by','not',
                  'but','from','have','has','had','all','can','do','did','will','would','should',
                  'may','no','so','if','up','out','just','than','them','then','its','also','how',
                  'after','before','now','here','there','where','when','what','which','who','each',
                  'very','been','more','some','could','other','into','only','new','these','two',
                  'about','over','such','your','our','their','his','her','she','he','we','you',
                  'me','my','i','am','—','...','+','=','→','←','↓','↗','⏎','✅','❌','⚠️','📌',
                  '```','ผม','เรา','ของ','แต่','เลย','ก็','อัน','ตัว','มา','ไป','กัน','แค่',
                  'ถ้า','ยัง','ต้อง','อะ','นะ','ดู','ตอน','เอา','แบบ','พี่','น้อง','คน'}

    word_pattern = re.compile(r'[a-zA-Z฀-๿]{2,}')

    day_terms = {}
    all_term_doc_count = Counter()

    for day, contents in sorted(docs.items()):
        text = ' '.join(contents).lower()
        words = word_pattern.findall(text)
        words = [w for w in words if w not in stop_words and len(w) > 1]
        tf = Counter(words)
        day_terms[day] = tf
        for w in set(words):
            all_term_doc_count[w] += 1

    n_docs = len(docs)
    print(f"\n{'='*60}")
    print(f"📊 TF-IDF Timeline — {n_docs} days, {sum(len(v) for v in docs.values())} messages")
    print(f"{'='*60}")

    for day in sorted(day_terms.keys()):
        tf = day_terms[day]
        msg_count = len(docs[day])
        tfidf = {}
        for term, count in tf.items():
            df = all_term_doc_count[term]
            idf = math.log(n_docs / (1 + df))
            tfidf[term] = count * idf

        top = sorted(tfidf.items(), key=lambda x: -x[1])[:5]
        terms_str = ' · '.join(f"{t}" for t, _ in top)
        print(f"  {day}  [{msg_count:>4} msgs]  {terms_str}")

def stats(db):
    total = db.execute("SELECT count(*) FROM messages").fetchone()[0]
    authors = db.execute("SELECT count(DISTINCT author_name) FROM messages").fetchone()[0]
    date_range = db.execute("SELECT min(timestamp), max(timestamp) FROM messages").fetchone()
    att = db.execute("SELECT sum(attachment_count) FROM messages").fetchone()[0] or 0
    days = db.execute("SELECT count(DISTINCT substr(timestamp, 1, 10)) FROM messages").fetchone()[0]

    print(f"\n📊 Gon Mirror Stats")
    print(f"  Messages:     {total}")
    print(f"  Authors:      {authors}")
    print(f"  Days:         {days}")
    print(f"  Attachments:  {att}")
    print(f"  Date range:   {date_range[0][:10]} → {date_range[1][:10]}")

    print(f"\n  Top authors:")
    for name, count in db.execute("SELECT author_name, count(*) as c FROM messages GROUP BY author_name ORDER BY c DESC LIMIT 10").fetchall():
        print(f"    {name}: {count}")

def search(db, query):
    results = db.execute(
        "SELECT m.author_name, substr(m.content, 1, 100), m.timestamp FROM messages m JOIN messages_fts f ON m.rowid = f.rowid WHERE messages_fts MATCH ? ORDER BY m.timestamp DESC LIMIT 10",
        (query,)
    ).fetchall()
    print(f"\n🔍 Search '{query}': {len(results)} results")
    for author, content, ts in results:
        print(f"  [{ts[:10]}] {author}: {content}")

if __name__ == "__main__":
    db = sqlite3.connect(DB_PATH)
    init_db(db)

    if len(sys.argv) < 2:
        print("Usage: mirror.py <command> [args]")
        print("  ingest <file> [channel_id]  — parse and store messages")
        print("  stats                       — show mirror stats")
        print("  tfidf                       — TF-IDF timeline by day")
        print("  search <query>              — FTS5 search")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "ingest":
        filepath = sys.argv[2]
        channel_id = sys.argv[3] if len(sys.argv) > 3 else "1512079809021214730"
        msgs = parse_file(filepath, channel_id)
        before = db.execute("SELECT count(*) FROM messages").fetchone()[0]
        store_messages(db, msgs)
        rebuild_fts(db)
        after = db.execute("SELECT count(*) FROM messages").fetchone()[0]
        print(f"✅ Ingested {len(msgs)} parsed, {after - before} new (total: {after})")
    elif cmd == "stats":
        stats(db)
    elif cmd == "tfidf":
        tfidf_by_day(db)
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        search(db, query)

    db.close()

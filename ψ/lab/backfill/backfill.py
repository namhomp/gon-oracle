#!/usr/bin/env python3
"""Gon Oracle — Discord Backfill (Workshop 05)
Fetch Discord messages via bot token, store in SQLite + FTS5.
"""
import sqlite3
import json
import time
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

DB_PATH = os.environ.get("BACKFILL_DB", os.path.join(os.path.dirname(__file__), "backfill.db"))
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

CHANNELS = {
    "1512079809021214730": "พระไตรปิฏก",
    "1510895726757023865": "hunter-room",
    "1512269802968973412": "gon-cave",
}

def init_db(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            author_name TEXT,
            content TEXT,
            timestamp TEXT NOT NULL,
            has_attachments INTEGER DEFAULT 0,
            indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cursors (
            channel_id TEXT PRIMARY KEY,
            last_message_id TEXT,
            last_fetched TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel_id);
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
    """)
    try:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(content, author_name, content=messages, content_rowid=rowid)")
    except sqlite3.OperationalError:
        pass

def discord_fetch(channel_id, after=None, limit=100):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    if after:
        url += f"&after={after}"
    req = Request(url, headers={"Authorization": f"Bot {BOT_TOKEN}"})
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
        return []

def backfill_channel(db, channel_id, channel_name):
    cursor_row = db.execute("SELECT last_message_id FROM cursors WHERE channel_id = ?", (channel_id,)).fetchone()
    cursor = cursor_row[0] if cursor_row else None
    total = 0
    print(f"\n[{channel_name}] Starting from cursor: {cursor or 'beginning'}")
    while True:
        messages = discord_fetch(channel_id, after=cursor)
        if not messages:
            break
        messages.sort(key=lambda m: m["id"])
        for msg in messages:
            db.execute(
                "INSERT OR IGNORE INTO messages (id, channel_id, author_id, author_name, content, timestamp, has_attachments) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg["id"], channel_id, msg["author"]["id"], msg["author"].get("username", ""), msg.get("content", ""), msg["timestamp"], 1 if msg.get("attachments") else 0),
            )
        cursor = messages[-1]["id"]
        db.execute("INSERT OR REPLACE INTO cursors (channel_id, last_message_id, last_fetched) VALUES (?, ?, ?)", (channel_id, cursor, datetime.utcnow().isoformat()))
        db.commit()
        total += len(messages)
        print(f"  +{len(messages)} messages (total: {total})")
        if len(messages) < 100:
            break
        time.sleep(1)
    print(f"[{channel_name}] Done — {total} new messages")
    return total

def rebuild_fts(db):
    db.execute("DELETE FROM messages_fts")
    db.execute("INSERT INTO messages_fts(rowid, content, author_name) SELECT rowid, content, author_name FROM messages")
    db.commit()

def search(db, query):
    rows = db.execute("SELECT m.author_name, m.content, m.timestamp FROM messages m JOIN messages_fts f ON m.rowid = f.rowid WHERE messages_fts MATCH ? ORDER BY m.timestamp DESC LIMIT 20", (query,)).fetchall()
    for author, content, ts in rows:
        print(f"  [{ts[:10]}] {author}: {content[:100]}")
    return rows

def stats(db):
    for ch_id, ch_name in CHANNELS.items():
        count = db.execute("SELECT COUNT(*) FROM messages WHERE channel_id = ?", (ch_id,)).fetchone()[0]
        cursor = db.execute("SELECT last_message_id, last_fetched FROM cursors WHERE channel_id = ?", (ch_id,)).fetchone()
        print(f"  {ch_name}: {count} messages (cursor: {cursor[0][:8] if cursor else 'none'}...)")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Set DISCORD_BOT_TOKEN environment variable")
        sys.exit(1)
    db = sqlite3.connect(DB_PATH)
    init_db(db)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "sync":
        print("=== 🪨 Gon Discord Backfill ===")
        grand_total = 0
        for ch_id, ch_name in CHANNELS.items():
            grand_total += backfill_channel(db, ch_id, ch_name)
        rebuild_fts(db)
        print(f"\n✅ Total: {grand_total} new messages indexed")
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        print(f"Searching: {query}")
        search(db, query)
    elif cmd == "stats":
        print("=== Backfill Stats ===")
        stats(db)
    db.close()

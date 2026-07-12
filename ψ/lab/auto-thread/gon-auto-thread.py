#!/usr/bin/env python3
"""
gon-auto-thread.py — Gon's auto_thread implementation (raw Discord REST)

Creates a thread on a Discord message via REST API.
Proves Gon can create threads programmatically — same exercise peers did.

Usage:
  python3 gon-auto-thread.py --prove <channel_id> <message_id>
  python3 gon-auto-thread.py --prove <channel_id> <message_id> --keep

--prove mode: create thread → post routing note → archive (cleanup)
--keep flag: skip archive step (leave thread visible)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API = "https://discord.com/api/v10"


def req(method, path, body=None):
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read()) if resp.read else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def create_thread(channel_id, message_id, name):
    return req("POST", f"/channels/{channel_id}/messages/{message_id}/threads", {
        "name": name[:100],
        "auto_archive_duration": 60,
    })


def post_message(channel_id, content):
    return req("POST", f"/channels/{channel_id}/messages", {
        "content": content,
    })


def archive_thread(thread_id):
    return req("PATCH", f"/channels/{thread_id}", {
        "archived": True,
    })


def prove(channel_id, message_id, keep=False):
    print(f"[gon-auto-thread] proving on channel={channel_id} message={message_id}")

    status, data = create_thread(channel_id, message_id, "🪨 gon auto_thread proof — เขียนเอง")
    if status not in (200, 201):
        print(f"✗ create thread failed: {status} {data}")
        sys.exit(1)

    thread_id = data["id"]
    print(f"✓ thread created: id={thread_id} name={data.get('name', '?')}")

    status2, _ = post_message(thread_id,
        "🪨 gon auto_thread proof\n"
        "- raw Discord REST (urllib, no discord.js)\n"
        "- create thread → post note → archive\n"
        "- pattern: เหมือนเพื่อนๆ (Tonk, bongbaeng, SomTor)\n"
        "🤖 ตอบโดย gon จาก Namhom → gon-oracle"
    )
    if status2 in (200, 201):
        print("✓ posted routing message into thread")
    else:
        print(f"⚠ post message: {status2}")

    if keep:
        print(f"PROVEN: auto_thread works — thread kept (--keep) 🪨")
    else:
        status3, _ = archive_thread(thread_id)
        if status3 == 200:
            print("✓ thread archived (cleanup)")
        else:
            print(f"⚠ archive: {status3} (bot may lack MANAGE_THREADS)")
        print("PROVEN: auto_thread works 🪨")

    return thread_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gon auto_thread — raw Discord REST")
    parser.add_argument("--prove", action="store_true", help="prove mode: create → post → archive")
    parser.add_argument("channel_id", help="Discord channel ID")
    parser.add_argument("message_id", help="Discord message ID to thread on")
    parser.add_argument("--keep", action="store_true", help="keep thread (don't archive)")
    args = parser.parse_args()

    if not TOKEN:
        print("error: set DISCORD_BOT_TOKEN env var")
        sys.exit(1)

    if args.prove:
        prove(args.channel_id, args.message_id, keep=args.keep)
    else:
        parser.print_help()

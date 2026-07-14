#!/usr/bin/env python3
"""
gon-blog-health.py — Blog health check for Gon Oracle

2x2 Health Matrix:
  Feed OK + Posts OK  = ✅ HEALTHY
  Feed OK + Posts BAD = ⚠️ PARTIAL
  Feed BAD            = ❌ FEED BROKEN

For single-page blogs (#anchor), verifies the anchor exists in home HTML
instead of checking per-post URLs (which always return 200 as false positive).

Usage:
  python3 gon-blog-health.py
  python3 gon-blog-health.py --base https://namhomp.github.io/gon-oracle
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error

DEFAULT_BASE = "https://namhomp.github.io/gon-oracle"


def fetch(url):
    try:
        r = urllib.request.Request(url)
        r.add_header("User-Agent", "gon-blog-health/1.0")
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def check_url(url):
    status, _ = fetch(url)
    return status


def extract_anchor(url):
    """Extract #anchor from url like https://example.com/#awakening"""
    m = re.search(r"#(.+)$", url)
    return m.group(1) if m else None


def run(base_url):
    print(f"🪨 Gon Blog Health Check")
    print(f"   Base: {base_url}")
    print()

    home_url = f"{base_url}/"
    feed_url = f"{base_url}/blog.json"

    home_status = check_url(home_url)
    print(f"  home    {home_url} → {home_status}")

    feed_status, feed_body = fetch(feed_url)
    print(f"  feed    {feed_url} → {feed_status}")

    feed_ok = feed_status == 200
    posts = []

    if feed_ok:
        try:
            data = json.loads(feed_body)
            posts = data.get("posts", [])
        except Exception as e:
            print(f"  ⚠ feed parse error: {e}")
            feed_ok = False

    print(f"  posts   {len(posts)} found")

    spec_fields = ["title", "description", "date", "datetime", "timestamp",
                   "tags", "author", "model", "url", "markdown"]
    missing_fields = set()
    for p in posts:
        for f in spec_fields:
            if f not in p:
                missing_fields.add(f)
    if missing_fields:
        print(f"  ⚠ FEED-SPEC v1 missing: {', '.join(sorted(missing_fields))}")
    else:
        print(f"  ✅ FEED-SPEC v1 fields complete")

    print()

    # Detect single-page blog: if posts have #anchor urls, verify anchors in HTML
    has_anchors = any(extract_anchor(p.get("url", "")) for p in posts)
    home_html = ""
    if has_anchors:
        print("  [single-page blog detected — verifying anchors in HTML]")
        _, home_html = fetch(home_url)

    post_results = []
    all_ok = True

    for p in posts:
        slug = p.get("slug", "?")
        post_url = p.get("url", "")
        anchor = extract_anchor(post_url)

        if anchor and home_html:
            # Single-page: check anchor exists in HTML as id="anchor"
            found = f'id="{anchor}"' in home_html
            icon = "✅" if found else "❌"
            method = "anchor"
            if not found:
                all_ok = False
            post_results.append((slug, found))
            print(f"  {icon} {slug} → id=\"{anchor}\" {'found' if found else 'NOT FOUND'} in HTML")
        elif post_url and not anchor:
            # Multi-page: check URL directly
            status = check_url(post_url)
            ok = status == 200
            if not ok:
                all_ok = False
            post_results.append((slug, ok))
            icon = "✅" if ok else "❌"
            print(f"  {icon} {slug} → {status}  {p.get('title', '')[:50]}")
        else:
            # No url field at all
            print(f"  ⚠ {slug} → no url field")
            all_ok = False
            post_results.append((slug, False))

    print()

    if feed_ok and all_ok and not missing_fields:
        verdict = "✅ HEALTHY (Feed SPEC-compliant, all posts verified)"
    elif feed_ok and all_ok:
        verdict = "🔵 FEED-OK (Feed reachable, posts verified, spec fields incomplete)"
    elif feed_ok and not all_ok:
        broken = sum(1 for _, ok in post_results if not ok)
        verdict = f"⚠️ PARTIAL (Feed OK, {broken}/{len(posts)} posts broken)"
    elif not feed_ok:
        verdict = "❌ FEED BROKEN (feed missing/broken)"
    else:
        verdict = "❌ DOWN"

    print(f"  Result: {verdict}")
    print()

    return 0 if feed_ok and all_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gon blog health check")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Blog base URL")
    args = parser.parse_args()
    sys.exit(run(args.base))

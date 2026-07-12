#!/usr/bin/env python3
"""
gon-blog-health.py — Blog health check for Gon Oracle

2x2 Health Matrix:
  Feed OK + Slugs OK  = ✅ HEALTHY
  Feed OK + Slugs BAD = ⚠️ PARTIAL (some posts broken)
  Feed BAD + Slugs OK = ⚠️ FEED BROKEN (posts exist but feed missing)
  Feed BAD + Slugs BAD = ❌ DOWN

Usage:
  python3 gon-blog-health.py
  python3 gon-blog-health.py --base https://namhomp.github.io/gon-oracle
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

DEFAULT_BASE = "https://namhomp.github.io/gon-oracle"


def check_url(url):
    try:
        r = urllib.request.Request(url, method="HEAD")
        r.add_header("User-Agent", "gon-blog-health/1.0")
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def run(base_url):
    print(f"🪨 Gon Blog Health Check")
    print(f"   Base: {base_url}")
    print()

    feed_url = f"{base_url}/blog.json"
    home_url = f"{base_url}/"

    home_status = check_url(home_url)
    print(f"  home    {home_url} → {home_status}")

    feed_status = check_url(feed_url)
    print(f"  feed    {feed_url} → {feed_status}")

    feed_ok = feed_status == 200
    posts = []

    if feed_ok:
        try:
            r = urllib.request.Request(feed_url)
            r.add_header("User-Agent", "gon-blog-health/1.0")
            with urllib.request.urlopen(r, timeout=10) as resp:
                data = json.loads(resp.read())
                posts = data.get("posts", [])
        except Exception as e:
            print(f"  ⚠ feed parse error: {e}")
            feed_ok = False

    print(f"  posts   {len(posts)} found")
    print()

    slug_results = []
    all_slugs_ok = True

    for p in posts:
        slug = p.get("slug", "?")
        post_url = f"{base_url}/#{slug}"
        status = check_url(post_url)
        ok = status == 200
        if not ok:
            all_slugs_ok = False
        slug_results.append((slug, p.get("title", "?"), status, ok))
        icon = "✅" if ok else "❌"
        print(f"  {icon} {slug} → {status}  {p.get('title', '')[:50]}")

    print()

    if feed_ok and all_slugs_ok:
        verdict = "✅ HEALTHY (Feed is OK, all slugs return 200)"
    elif feed_ok and not all_slugs_ok:
        broken = sum(1 for _, _, _, ok in slug_results if not ok)
        verdict = f"⚠️ PARTIAL (Feed OK, {broken}/{len(posts)} slugs broken)"
    elif not feed_ok and all_slugs_ok:
        verdict = "⚠️ FEED BROKEN (posts may exist but feed missing/broken)"
    else:
        verdict = "❌ DOWN (feed broken, slugs broken)"

    print(f"  Result: {verdict}")
    print()

    return 0 if feed_ok and all_slugs_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gon blog health check")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Blog base URL")
    args = parser.parse_args()
    sys.exit(run(args.base))

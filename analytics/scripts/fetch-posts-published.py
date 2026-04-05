#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Count blog posts published in the last 28 days.

Scans posts/**/index.qmd files, parses YAML frontmatter, and counts posts
where draft: false and date is within the last 28 days.

Usage:
  uv run scripts/fetch-posts-published.py
  uv run scripts/fetch-posts-published.py --test    # exit 1 if error
  uv run scripts/fetch-posts-published.py --fixture # offline mode (reads fixtures/posts_published_28d.txt)

Output (same format as fetch-metrics.py):
  {"fetched_at": "...", "metrics": {"posts_published_28d": {"value": 2, "status": "ok", "fetched_at": "..."}}}
"""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from datetime import datetime, timezone
from pathlib import Path

METRIC_NAME = "posts_published_28d"
WINDOW_DAYS = 28


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_frontmatter(text: str) -> dict:
    """Extract key: value pairs from YAML frontmatter block."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).splitlines():
        kv = re.match(r"^(\w+):\s*(.+)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm


def count_recent_posts(posts_dir: Path, cutoff: date) -> int:
    count = 0
    for qmd_file in posts_dir.glob("**/index.qmd"):
        text = qmd_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)

        draft = fm.get("draft", "false").lower()
        if draft == "true":
            continue

        raw_date = fm.get("date", "")
        try:
            post_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        if post_date >= cutoff:
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Count blog posts published in last 28 days")
    parser.add_argument("--test", action="store_true", help="Exit 1 if metric fails")
    parser.add_argument("--fixture", action="store_true", help="Use saved fixture instead of scanning")
    parser.add_argument(
        "--fixture-dir",
        default=None,
        help="Fixture directory (default: ../fixtures relative to this script)",
    )
    parser.add_argument(
        "--posts-dir",
        default=None,
        help="Path to posts directory (default: ../../posts relative to this script)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    fixture_dir = Path(args.fixture_dir) if args.fixture_dir else script_dir / ".." / "fixtures"
    fixture_dir = fixture_dir.resolve()
    posts_dir = Path(args.posts_dir) if args.posts_dir else script_dir / ".." / ".." / "posts"
    posts_dir = posts_dir.resolve()

    fetched_at = now_iso()

    try:
        if args.fixture:
            fixture_path = fixture_dir / f"{METRIC_NAME}.txt"
            if not fixture_path.exists():
                raise FileNotFoundError(f"Fixture not found: {fixture_path}")
            print(f"[{METRIC_NAME}] loading fixture ...", file=sys.stderr)
            value = int(fixture_path.read_text().strip())
        else:
            if not posts_dir.exists():
                raise FileNotFoundError(f"Posts directory not found: {posts_dir}")
            cutoff = date.today() - timedelta(days=WINDOW_DAYS)
            print(f"[{METRIC_NAME}] scanning {posts_dir} for posts since {cutoff} ...", file=sys.stderr)
            value = count_recent_posts(posts_dir, cutoff)
            print(f"[{METRIC_NAME}] extracted value={value!r}", file=sys.stderr)

        result = {"value": value, "status": "ok", "fetched_at": fetched_at}

    except Exception as e:
        print(f"[{METRIC_NAME}] error: {e}", file=sys.stderr)
        result = {"value": None, "status": "error", "error": str(e), "fetched_at": fetched_at}

    output = {"fetched_at": now_iso(), "metrics": {METRIC_NAME: result}}
    print(json.dumps(output, indent=2))

    if args.test and result["status"] != "ok":
        print(f"\n[--test] FAILED: {METRIC_NAME}", file=sys.stderr)
        sys.exit(1)
    elif args.test:
        print(f"[--test] {METRIC_NAME} passed.", file=sys.stderr)


if __name__ == "__main__":
    main()

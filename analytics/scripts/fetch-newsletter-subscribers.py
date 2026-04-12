#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Fetch total newsletter subscriber count from Supabase.

Queries the newsletter_subscribers table using the Supabase REST API with
Prefer: count=exact to get the count efficiently without fetching all rows.

Auth: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY) env vars.

Usage:
  uv run scripts/fetch-newsletter-subscribers.py
  uv run scripts/fetch-newsletter-subscribers.py --test    # exit 1 if error
  uv run scripts/fetch-newsletter-subscribers.py --fixture # offline mode

Output (same format as fetch-metrics.py):
  {"fetched_at": "...", "metrics": {"newsletter_subscriber_count": {"value": 42, "status": "ok", "fetched_at": "..."}}}
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

METRIC_NAME = "newsletter_subscriber_count"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_supabase_creds() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url:
        raise RuntimeError("SUPABASE_URL env var not set")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY) env var not set")
    return url, key


def fetch_subscriber_count(supabase_url: str, service_key: str) -> int:
    endpoint = f"{supabase_url}/rest/v1/newsletter_subscribers?select=*"
    req = urllib.request.Request(
        endpoint,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Prefer": "count=exact",
            "User-Agent": "metric-extractor/1.0",
        },
        method="HEAD",
    )
    with urllib.request.urlopen(req) as resp:
        content_range = resp.headers.get("Content-Range", "")

    # Content-Range: 0-N/TOTAL or */TOTAL
    if "/" in content_range:
        total_str = content_range.split("/")[-1]
        if total_str.isdigit():
            return int(total_str)

    raise RuntimeError(f"Could not parse count from Content-Range header: {content_range!r}")


def main():
    parser = argparse.ArgumentParser(description="Fetch newsletter subscriber count from Supabase")
    parser.add_argument("--test", action="store_true", help="Exit 1 if metric fails")
    parser.add_argument("--fixture", action="store_true", help="Use saved fixture instead of live HTTP")
    parser.add_argument(
        "--fixture-dir",
        default=None,
        help="Fixture directory (default: ../fixtures relative to this script)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    fixture_dir = Path(args.fixture_dir) if args.fixture_dir else script_dir / ".." / "fixtures"
    fixture_dir = fixture_dir.resolve()

    fetched_at = now_iso()

    try:
        if args.fixture:
            fixture_path = fixture_dir / f"{METRIC_NAME}.txt"
            if not fixture_path.exists():
                raise FileNotFoundError(f"Fixture not found: {fixture_path}")
            print(f"[{METRIC_NAME}] loading fixture ...", file=sys.stderr)
            value = int(fixture_path.read_text().strip())
        else:
            supabase_url, service_key = get_supabase_creds()
            print(f"[{METRIC_NAME}] querying Supabase newsletter_subscribers ...", file=sys.stderr)
            value = fetch_subscriber_count(supabase_url, service_key)
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

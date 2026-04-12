#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-auth[requests]"]
# ///
"""
Fetch top 5 traffic-acquisition source/medium from GA4 (last 7 days).

Queries sessionSourceMedium dimension ranked by sessions descending.

Auth: service account at credentials/ga4-service-account.json

Usage:
  uv run scripts/fetch-ga4-top-sources.py
  uv run scripts/fetch-ga4-top-sources.py --test    # exit 1 if error

Output (same format as fetch-metrics.py):
  {"fetched_at": "...", "metrics": {"ga4_top_sources": {"value": "1. google / organic: 450\\n...", "status": "ok", ...}}}
"""

import json
import sys
import urllib.request
import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

PROPERTY_ID = "464728949"
METRIC_NAME = "ga4_top_sources"
TOP_N = 5


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_credentials(script_dir: Path):
    import google.oauth2.service_account
    import google.auth.transport.requests

    creds_path = (script_dir / ".." / "credentials" / "ga4-service-account.json").resolve()
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Service account credentials not found: {creds_path}\n"
            "Download from GCP Console → IAM → Service Accounts → Keys"
        )
    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    credentials = google.oauth2.service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=scopes
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials


def fetch_top_sources(credentials) -> list:
    today = date.today()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY_ID}:runReport"
    body = {
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "dimensions": [{"name": "sessionSourceMedium"}],
        "metrics": [{"name": "sessions"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": TOP_N,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    rows = result.get("rows", [])
    if not rows:
        return []

    entries = []
    for row in rows:
        source_medium = row["dimensionValues"][0]["value"]
        sessions = int(row["metricValues"][0]["value"])
        entries.append([source_medium, sessions])
    return entries


def main():
    parser = argparse.ArgumentParser(description="Fetch top 5 GA4 traffic source/medium")
    parser.add_argument("--test", action="store_true", help="Exit 1 if metric fails")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    fetched_at = now_iso()

    try:
        print(f"[{METRIC_NAME}] fetching top {TOP_N} source/medium from GA4 ...", file=sys.stderr)
        credentials = get_credentials(script_dir)
        value = fetch_top_sources(credentials)
        for i, (src, n) in enumerate(value, 1):
            print(f"[{METRIC_NAME}]   {i}. {src}: {n}", file=sys.stderr)
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

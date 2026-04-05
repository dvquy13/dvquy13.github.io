#!/usr/bin/env python3
"""
Merge and display analytics metrics as a terminal dashboard.

Reads JSON metric outputs from stdin (one JSON blob per line or piped files),
merges them, and prints a formatted dashboard.

Usage:
  # Merge two fetch outputs and display
  python scripts/display-dashboard.py ga4.json giscus.json

  # Or pipe merged JSON
  echo '{"fetched_at":"...","metrics":{...}}' | python scripts/display-dashboard.py
"""

import json
import sys
from datetime import datetime


DISPLAY_CONFIG = {
    "ga4_total_users": {
        "label": "Visitors (30d)",
        "icon": "👥",
        "format": lambda v: f"{v:,}",
    },
    "giscus_total_reactions": {
        "label": "Total Reactions",
        "icon": "❤️ ",
        "format": lambda v: f"{v:,}",
    },
}


def merge_metric_files(paths: list[str]) -> dict:
    merged_metrics = {}
    fetched_at = None
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        merged_metrics.update(data.get("metrics", {}))
        fetched_at = fetched_at or data.get("fetched_at")
    return {"fetched_at": fetched_at, "metrics": merged_metrics}


def display(snapshot: dict) -> None:
    metrics = snapshot.get("metrics", {})
    fetched_at = snapshot.get("fetched_at", "")

    try:
        dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        ts = dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        ts = fetched_at

    width = 38
    print()
    print("📊 Blog Analytics Dashboard")
    print("=" * width)

    for metric_name, cfg in DISPLAY_CONFIG.items():
        entry = metrics.get(metric_name)
        if entry is None:
            continue
        if entry.get("status") == "error":
            display_val = "ERROR (see above)"
        else:
            raw = entry.get("value")
            display_val = cfg["format"](raw) if raw is not None else "—"
        label = f"{cfg['icon']}  {cfg['label']}"
        print(f"{label:<22}  {display_val:>10}")

    print("=" * width)
    print(f"{'Updated:':<22}  {ts:>10}")
    print()


def main():
    if len(sys.argv) > 1:
        snapshot = merge_metric_files(sys.argv[1:])
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("No input provided.", file=sys.stderr)
            sys.exit(1)
        snapshot = json.loads(raw)

    display(snapshot)


if __name__ == "__main__":
    main()

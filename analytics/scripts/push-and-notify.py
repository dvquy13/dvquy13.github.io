#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Read fetch output JSON from stdin, append snapshot to a JSONL file, send Telegram alerts.

Usage:
    uv run scripts/fetch-metrics.py | uv run scripts/push-and-notify.py

Env vars:
    METRICS_JSONL      — path to metrics JSONL file (default: metrics.jsonl in analytics/ dir)
    TELEGRAM_BOT_TOKEN — optional; skipped if absent
    TELEGRAM_CHAT_ID   — optional; skipped if absent
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml


# ── JSONL storage ──────────────────────────────────────────────────────────────

def jsonl_get_latest(path: Path) -> dict | None:
    """Return the last snapshot in the JSONL file, or None if empty/missing."""
    if not path.exists():
        return None
    last = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                last = line
    return json.loads(last) if last else None


def jsonl_append(path: Path, snapshot: dict) -> None:
    """Append one snapshot as a JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps({"fetched_at": snapshot["fetched_at"], "metrics": snapshot["metrics"]}) + "\n")


# ── Telegram ───────────────────────────────────────────────────────────────────

def telegram_send(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        _ = resp.read()


# ── Alert evaluation ───────────────────────────────────────────────────────────

def check_alerts(alert_cfg: list, current: dict, previous: dict | None) -> list[str]:
    messages = []
    current_metrics = current.get("metrics", {})
    prev_metrics = (previous or {}).get("metrics", {})

    for rule in alert_cfg:
        rule_type = rule.get("type")

        if rule_type == "failure":
            failed = [
                f"  {name}: {m.get('error', 'unknown error')}"
                for name, m in current_metrics.items()
                if m.get("status") == "error"
            ]
            if failed:
                body = "\n".join(failed)
                messages.append(f"⚠️ Metrics fetch failed\n{body}")

        elif rule_type == "metric_change":
            metric = rule["metric"]
            label = rule.get("label", metric)
            direction = rule.get("direction", "any")
            min_delta = rule.get("min_delta", 1)

            curr_entry = current_metrics.get(metric)
            prev_entry = prev_metrics.get(metric)

            if not curr_entry or curr_entry.get("status") != "ok":
                continue
            if not prev_entry or prev_entry.get("status") != "ok":
                continue

            curr_val = curr_entry["value"]
            prev_val = prev_entry["value"]

            try:
                delta = float(curr_val) - float(prev_val)
            except (TypeError, ValueError):
                continue

            abs_delta = abs(delta)
            if abs_delta < min_delta:
                continue

            if direction == "increase" and delta <= 0:
                continue
            if direction == "decrease" and delta >= 0:
                continue

            sign = "+" if delta > 0 else ""
            arrow = "📈" if delta > 0 else "📉"
            messages.append(
                f"{arrow} {label}: {prev_val} → {curr_val} ({sign}{delta:g})"
            )

    return messages


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # 1. Read fetch output from stdin
    raw = sys.stdin.read().strip()
    if not raw:
        print("[push-and-notify] stdin is empty — nothing to do", file=sys.stderr)
        sys.exit(1)
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[push-and-notify] invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Load alerts config
    script_dir = Path(__file__).parent
    alerts_path = (script_dir / ".." / "alerts.yaml").resolve()
    if not alerts_path.exists():
        print(f"[push-and-notify] alerts config not found: {alerts_path}", file=sys.stderr)
        sys.exit(1)
    with open(alerts_path) as f:
        alerts_cfg = yaml.safe_load(f)

    tg_cfg = alerts_cfg.get("telegram", {})
    bot_token = os.environ.get(tg_cfg.get("bot_token_env", "TELEGRAM_BOT_TOKEN"), "")
    chat_id = os.environ.get(tg_cfg.get("chat_id_env", "TELEGRAM_CHAT_ID"), "")
    alert_rules = alerts_cfg.get("alerts", [])

    # 3. JSONL: read previous snapshot, append current
    default_jsonl = (script_dir / ".." / "metrics.jsonl").resolve()
    jsonl_path = Path(os.environ.get("METRICS_JSONL", str(default_jsonl)))

    previous = jsonl_get_latest(jsonl_path)
    print(f"[push-and-notify] previous snapshot: {(previous or {}).get('fetched_at', 'none')}", file=sys.stderr)

    jsonl_append(jsonl_path, snapshot)
    print(f"[push-and-notify] appended snapshot fetched_at={snapshot['fetched_at']} to {jsonl_path}", file=sys.stderr)

    # 4. Evaluate alerts
    messages = check_alerts(alert_rules, snapshot, previous)

    # 5. Send Telegram messages
    if messages:
        if bot_token and chat_id:
            for msg in messages:
                try:
                    telegram_send(bot_token, chat_id, msg)
                    print(f"[push-and-notify] Telegram sent: {msg[:60]!r}", file=sys.stderr)
                except Exception as e:
                    print(f"[push-and-notify] WARNING: Telegram send failed: {e}", file=sys.stderr)
        else:
            print("[push-and-notify] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping notifications", file=sys.stderr)
            for msg in messages:
                print(f"[push-and-notify] (unsent) {msg}", file=sys.stderr)
    else:
        print("[push-and-notify] no alerts triggered", file=sys.stderr)


if __name__ == "__main__":
    main()

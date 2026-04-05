#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Read fetch output JSON from stdin, write snapshot to Supabase, send Telegram alerts.

Usage:
    uv run scripts/fetch-metrics.py | uv run scripts/push-and-notify.py

Env vars required:
    SUPABASE_URL              — e.g. https://wzacvfhfpqhdutqfcofz.supabase.co
    SUPABASE_SERVICE_ROLE_KEY — service role key (bypasses RLS for INSERT)
    TELEGRAM_BOT_TOKEN        — optional; skipped if absent
    TELEGRAM_CHAT_ID          — optional; skipped if absent
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml


# ── Supabase ───────────────────────────────────────────────────────────────────

def supabase_headers(key: str) -> dict:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def supabase_get_latest(supabase_url: str, key: str) -> dict | None:
    """Return the most recent metrics_snapshots row, or None if table is empty."""
    url = (
        supabase_url.rstrip("/")
        + "/rest/v1/metrics_snapshots"
        "?order=fetched_at.desc&limit=1&select=fetched_at,metrics"
    )
    req = urllib.request.Request(url, headers=supabase_headers(key))
    with urllib.request.urlopen(req) as resp:
        rows = json.loads(resp.read())
    return rows[0] if rows else None


def supabase_insert(supabase_url: str, key: str, snapshot: dict) -> None:
    """INSERT one row into metrics_snapshots."""
    url = supabase_url.rstrip("/") + "/rest/v1/metrics_snapshots"
    payload = json.dumps({
        "fetched_at": snapshot["fetched_at"],
        "metrics": snapshot["metrics"],
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={**supabase_headers(key), "Prefer": "return=minimal"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        _ = resp.read()  # consume response


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
    alerts_path = script_dir / ".." / "configs" / "alerts.yaml"
    alerts_path = alerts_path.resolve()
    if not alerts_path.exists():
        print(f"[push-and-notify] alerts config not found: {alerts_path}", file=sys.stderr)
        sys.exit(1)
    with open(alerts_path) as f:
        alerts_cfg = yaml.safe_load(f)

    tg_cfg = alerts_cfg.get("telegram", {})
    bot_token = os.environ.get(tg_cfg.get("bot_token_env", "TELEGRAM_BOT_TOKEN"), "")
    chat_id = os.environ.get(tg_cfg.get("chat_id_env", "TELEGRAM_CHAT_ID"), "")
    alert_rules = alerts_cfg.get("alerts", [])

    # 3. Supabase: get previous snapshot + insert current
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    previous = None
    if supabase_url and supabase_key:
        try:
            previous = supabase_get_latest(supabase_url, supabase_key)
            print(f"[push-and-notify] previous snapshot: {(previous or {}).get('fetched_at', 'none')}", file=sys.stderr)
        except Exception as e:
            print(f"[push-and-notify] WARNING: could not fetch previous snapshot: {e}", file=sys.stderr)

        try:
            supabase_insert(supabase_url, supabase_key, snapshot)
            print(f"[push-and-notify] inserted snapshot fetched_at={snapshot['fetched_at']}", file=sys.stderr)
        except Exception as e:
            print(f"[push-and-notify] ERROR: failed to insert snapshot: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[push-and-notify] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — skipping DB write", file=sys.stderr)

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

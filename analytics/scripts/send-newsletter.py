#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "markdown"]
# ///
"""
Send a newsletter email to all subscribers for a given blog post.

Usage:
    uv run analytics/scripts/send-newsletter.py <path/to/post/index.qmd> [--dry-run]

Env vars (required):
    SUPABASE_URL              — Supabase project URL
    SUPABASE_SECRET_KEY       — Supabase secret key (falls back to SUPABASE_SERVICE_ROLE_KEY)
    RESEND_API_KEY            — Resend API key

Dry-run mode prints the emails that would be sent without calling Resend.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import markdown
import yaml

SITE_URL = "https://dvquys.com"
FROM_ADDRESS = "DvQ <hello@dvquys.com>"
UNSUBSCRIBE_BASE = f"{SITE_URL}/unsubscribe.html"
RESEND_BATCH_URL = "https://api.resend.com/emails/batch"
BATCH_SIZE = 100


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_qmd(path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, markdown body string)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    # Find closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body   = text[end + 4:].strip()
    fm = yaml.safe_load(fm_raw) or {}
    return fm, body


def derive_post_url(qmd_path: Path) -> str:
    """Convert a .qmd file path to its published URL."""
    # Resolve to a path relative to the repo root (we walk up to find _quarto.yml)
    resolved = qmd_path.resolve()
    repo_root = resolved
    while repo_root != repo_root.parent:
        if (repo_root / "_quarto.yml").exists():
            break
        repo_root = repo_root.parent

    try:
        rel = resolved.relative_to(repo_root)
    except ValueError:
        rel = resolved

    if rel.name == "index.qmd":
        return f"{SITE_URL}/{rel.parent}/"
    return f"{SITE_URL}/{rel.with_suffix('.html')}"


def build_html(fm: dict, body_md: str, post_url: str, unsubscribe_url: str) -> str:
    title    = fm.get("title", "New post")
    subtitle = fm.get("subtitle", "")
    date_str = str(fm.get("date", ""))

    # Strip Quarto-specific shortcodes/callouts that won't render in email
    body_md = re.sub(r"^:::\s*\{[^}]*\}.*?^:::", "", body_md, flags=re.MULTILINE | re.DOTALL)
    body_md = re.sub(r"^\{\{<.*?>\}\}", "", body_md, flags=re.MULTILINE)

    body_html = markdown.markdown(body_md, extensions=["fenced_code", "tables"])

    # Rewrite relative image src to absolute URLs so they render in email clients
    def make_absolute(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            return m.group(0)
        src = src.lstrip("./")
        return f'src="{post_url.rstrip("/")}/{src}"'
    body_html = re.sub(r'src="([^"]*)"', make_absolute, body_html)

    subtitle_block = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    date_block     = f'<p class="date">{date_str}</p>'     if date_str  else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body      {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               font-size: 16px; line-height: 1.65; color: #222;
               max-width: 600px; margin: 0 auto; padding: 24px 20px; }}
  h1        {{ font-size: 22px; line-height: 1.3; margin: 8px 0 4px; }}
  .subtitle {{ color: #555; font-size: 15px; margin: 0 0 20px; }}
  .date     {{ color: #888; font-size: 13px; margin: 0 0 4px; }}
  .cta      {{ display: inline-block; background: #0057a3; color: #fff !important;
               text-decoration: none; padding: 10px 20px; border-radius: 5px; margin: 20px 0; }}
  hr        {{ border: none; border-top: 1px solid #eee; margin: 32px 0; }}
  .footer   {{ font-size: 12px; color: #888; }}
  .footer a {{ color: #888; }}
  img       {{ max-width: 100%; height: auto; }}
  pre       {{ background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 13px; }}
  code      {{ background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 13px; }}
  pre code  {{ background: none; padding: 0; }}
</style>
</head>
<body>
{date_block}
<h1>{title}</h1>
{subtitle_block}
<a href="{post_url}" class="cta">Read on dvquys.com →</a>

<div class="post-content">
{body_html}
</div>

<hr>
<div class="footer">
  <p>
    You're receiving this because you subscribed at
    <a href="{SITE_URL}">dvquys.com</a>.<br>
    <a href="{unsubscribe_url}">Unsubscribe</a>
  </p>
</div>
</body>
</html>"""


# ── Supabase ───────────────────────────────────────────────────────────────────

def fetch_subscribers(supabase_url: str, service_key: str) -> list[dict]:
    """Return list of {email, unsubscribe_token} dicts."""
    endpoint = (
        f"{supabase_url}/rest/v1/newsletter_subscribers"
        "?select=email,unsubscribe_token"
    )
    req = urllib.request.Request(
        endpoint,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# ── Resend ─────────────────────────────────────────────────────────────────────

def send_batch(emails: list[dict], api_key: str) -> list[dict]:
    """Send a batch of up to BATCH_SIZE emails via Resend. Returns API response list."""
    payload = json.dumps(emails).encode()
    req = urllib.request.Request(
        RESEND_BATCH_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Resend sits behind Cloudflare WAF which blocks Python-urllib/3.x by default
            "User-Agent": "dvquys-newsletter/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qmd_file", help="Path to the .qmd post file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print emails without sending")
    args = parser.parse_args()

    qmd_path = Path(args.qmd_file)
    if not qmd_path.exists():
        print(f"ERROR: file not found: {qmd_path}", file=sys.stderr)
        sys.exit(1)

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_key  = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    resend_key   = os.environ.get("RESEND_API_KEY", "")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set", file=sys.stderr)
        sys.exit(1)
    if not resend_key and not args.dry_run:
        print("ERROR: RESEND_API_KEY must be set (or use --dry-run)", file=sys.stderr)
        sys.exit(1)

    # Parse post
    fm, body_md = parse_qmd(qmd_path)
    post_url = derive_post_url(qmd_path)
    print(f"Post:  {fm.get('title', '(untitled)')}")
    print(f"URL:   {post_url}")

    # Fetch subscribers
    subscribers = fetch_subscribers(supabase_url, service_key)
    print(f"Subscribers: {len(subscribers)}")
    if not subscribers:
        print("No subscribers — nothing to send.")
        return

    # Build email payloads
    payloads: list[dict] = []
    for sub in subscribers:
        unsubscribe_url = f"{UNSUBSCRIBE_BASE}?token={sub['unsubscribe_token']}"
        html = build_html(fm, body_md, post_url, unsubscribe_url)
        payloads.append({
            "from": FROM_ADDRESS,
            "to": [sub["email"]],
            "subject": fm.get("title", "New post from DvQ"),
            "html": html,
            "headers": {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        })

    if args.dry_run:
        print("\n--- DRY RUN: emails that would be sent ---")
        for p in payloads:
            print(f"  to={p['to'][0]}  subject={p['subject']!r}")
        print(f"\nTotal: {len(payloads)} email(s). Not sent.")
        return

    # Send in batches
    sent = failed = 0
    for i in range(0, len(payloads), BATCH_SIZE):
        batch = payloads[i : i + BATCH_SIZE]
        try:
            results = send_batch(batch, resend_key)
            # Resend batch returns {"data": [...]} or a list directly
            items = results.get("data", results) if isinstance(results, dict) else results
            for item in items:
                if item.get("id"):
                    sent += 1
                else:
                    failed += 1
                    print(f"  FAILED: {item}", file=sys.stderr)
        except Exception as e:
            print(f"  Batch {i//BATCH_SIZE + 1} error: {e}", file=sys.stderr)
            failed += len(batch)

    print(f"\nSent: {sent}  Failed: {failed}")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Validate RSS feed using W3C Feed Validation Service.
# Usage:
#   ./scripts/validate-rss.sh              # validate local build (docs/index.xml)
#   ./scripts/validate-rss.sh --live       # validate deployed feed at dvquys.com

set -euo pipefail

LIVE=false
if [[ "${1:-}" == "--live" ]]; then
  LIVE=true
fi

if $LIVE; then
  echo "Validating live feed: https://dvquys.com/index.xml"
  CB=$(date +%s)
  RESPONSE=$(curl -s "https://validator.w3.org/feed/check.cgi?url=https%3A%2F%2Fdvquys.com%2Findex.xml%3Fcb%3D${CB}&output=soap12")
else
  FEED="$(dirname "$0")/../docs/index.xml"
  if [[ ! -f "$FEED" ]]; then
    echo "ERROR: Local feed not found at $FEED — run 'make build' first."
    exit 1
  fi
  echo "Validating local feed: $FEED"
  RESPONSE=$(curl -s -X POST "https://validator.w3.org/feed/check.cgi?output=soap12" \
    --data-urlencode "rawdata@$FEED")
fi

TMPFILE=$(mktemp)
printf '%s' "$RESPONSE" > "$TMPFILE"
python3 - "$TMPFILE" <<'EOF'
import sys, re, os

content = open(sys.argv[1]).read()
os.unlink(sys.argv[1])

def extract_text(tag, xml):
    """Extract text content of all occurrences of a tag."""
    return re.findall(rf'<{tag}>(.*?)</{tag}>', xml, re.DOTALL)

def clean(s):
    return re.sub(r'<[^>]+>', '', s).strip()

errors_xml   = re.findall(r'<error>(.*?)</error>', content, re.DOTALL)
warnings_xml = re.findall(r'<warning>(.*?)</warning>', content, re.DOTALL)

def parse_issue(xml_block):
    def get(tag):
        m = re.search(rf'<{tag}>(.*?)</{tag}>', xml_block, re.DOTALL)
        return clean(m.group(1)) if m else ''
    return {
        'type':    get('type'),
        'line':    get('line'),
        'col':     get('column'),
        'text':    get('text'),
        'count':   get('count'),
        'element': get('element'),
        'context': get('value'),
    }

errors   = [parse_issue(x) for x in errors_xml]
warnings = [parse_issue(x) for x in warnings_xml]

FAIL = False

# ── Errors (always fail) ────────────────────────────────────────────────────
if errors:
    FAIL = True
    print(f"\n✗ ERRORS ({len(errors)}):")
    for e in errors:
        count_str = f" [{e['count']}x]" if e['count'] and e['count'] != '1' else ''
        print(f"  Line {e['line']}: {e['text']}{count_str}")
        if e['context']:
            print(f"    → {e['context'][:100]}")

# ── Warnings (checked selectively) ─────────────────────────────────────────
ALLOWED_WARNINGS = {
    'ContainsRelRef',        # relative URLs in description — cosmetic
    'SecurityRisk',          # iframes — intentional YouTube embeds
    'SelfDoesntMatchLocation',  # expected when POSTing local feed (atom:link points to live URL)
}

DISALLOWED_WARNINGS = {
    'DangerousStyleAttr',  # style="null" from broken syntax highlighting
}

blocking_warnings = [w for w in warnings if w['type'] in DISALLOWED_WARNINGS]
allowed_warnings  = [w for w in warnings if w['type'] in ALLOWED_WARNINGS]
unknown_warnings  = [w for w in warnings if w['type'] not in ALLOWED_WARNINGS and w['type'] not in DISALLOWED_WARNINGS]

if blocking_warnings:
    FAIL = True
    print(f"\n✗ BLOCKING WARNINGS ({len(blocking_warnings)}):")
    for w in blocking_warnings:
        count_str = f" [{w['count']}x]" if w['count'] and w['count'] != '1' else ''
        print(f"  [{w['type']}] Line {w['line']}: {w['text']}{count_str}")
        if w['context']:
            print(f"    → {w['context'][:100]}")

if unknown_warnings:
    FAIL = True
    print(f"\n✗ UNKNOWN WARNINGS (review needed) ({len(unknown_warnings)}):")
    for w in unknown_warnings:
        print(f"  [{w['type']}] Line {w['line']}: {w['text']}")

if allowed_warnings:
    print(f"\n~ Allowed warnings ({len(allowed_warnings)}):")
    for w in allowed_warnings:
        count_str = f" [{w['count']}x]" if w['count'] and w['count'] != '1' else ''
        print(f"  [{w['type']}] {w['text']}{count_str}")

if FAIL:
    print("\n✗ RSS feed validation FAILED")
    sys.exit(1)
else:
    print("\n✓ RSS feed validation PASSED")
    sys.exit(0)
EOF

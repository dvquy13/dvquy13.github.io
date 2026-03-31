#!/usr/bin/env bash
# Post-process docs/index.xml after quarto render.
# Fixes Quarto's github highlight theme emitting `color: null` and
# `background-color: null` as literal CSS values in code block spans.

set -euo pipefail

FEED="$(dirname "$0")/../docs/index.xml"

if [[ ! -f "$FEED" ]]; then
  echo "ERROR: $FEED not found — run 'make build' first."
  exit 1
fi

python3 - "$FEED" <<'EOF'
import sys, re

path = sys.argv[1]
with open(path) as f:
    content = f.read()

before = len(re.findall(r'(?:background-color|color): null;', content))

# Remove `color: null;` and `background-color: null;` CSS declarations.
# These come from Quarto's github highlight theme for tokens with no defined color.
content = re.sub(r'(?:background-color|color): null;\n?', '', content)

after = len(re.findall(r'(?:background-color|color): null;', content))

with open(path, 'w') as f:
    f.write(content)

print(f"Cleaned {before - after} null CSS declarations from {path}")
EOF

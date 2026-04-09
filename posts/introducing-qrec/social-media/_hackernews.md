---
link:
notes:
  - Post Tuesday–Thursday, 8–11 AM US Eastern
  - Respond within 60 minutes of posting
  - Disclosure: state clearly you built this
---

## Title

Show HN: qrec – local session recall for Claude Code

## First Comment

I built this after realizing a thousand Claude Code session files were on my machine but effectively unsearchable: raw JSONL packed with tool calls and thinking blocks. qrec strips those down to clean user-assistant threads, indexes them with hybrid search (BM25 + semantic + RRF), and lets an agent retrieve past decisions on demand without touching your main token budget.

Blog post: https://dvquys.com/posts/introducing-qrec/?utm_source=hackernews&utm_medium=social&utm_campaign=introducing-qrec
GitHub: https://github.com/dvquy13/qrec

Curious whether the session-handoff use case—opening a fresh session and recovering context from a capped one—translates to workflows beyond Claude Code.


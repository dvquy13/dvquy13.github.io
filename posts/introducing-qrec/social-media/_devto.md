---
title: Helping Claude Code Remember: How I Built a Local Session Recall Tool
published: true
description: Every Claude Code session starts fresh. After 1,000+ sessions, I built qrec — a local hybrid search index that lets you recover past decisions without spending extra tokens.
tags: claudeai, devtools, opensource, ai, python
cover_image:
canonical_url: https://dvquys.com/posts/introducing-qrec/?utm_source=devto&utm_medium=crosspost&utm_campaign=introducing-qrec
---

Every Claude Code session starts fresh. That's fine at first, but 1,000+ sessions in, I had weeks of decisions technically on disk and practically unreachable. The sessions live in `~/.claude/projects/` as raw JSONL packed with tool calls and thinking blocks—readable in theory, but nobody is trawling through that.

I built [qrec](https://github.com/dvquy13/qrec): a local session recall tool that strips the noise, indexes everything with hybrid search (BM25 + semantic + RRF), and lets a Claude Code agent retrieve past decisions on demand. No tokens spent; your data stays on your machine.

The use case I didn't design for ended up being the most useful: context handoff. Deep in a 200-turn session about to hit the context limit, I opened a fresh one and typed "pick up context from the previous session." It came back with the exact decision we'd been circling, and we continued at ~15% context usage.

The full post covers what I tried first (QMD, claude-mem), the bets I made on transparency and local-only execution, and—honestly—why the eval is still unsolved.

**[Read it on my blog →](https://dvquys.com/posts/introducing-qrec/?utm_source=devto&utm_medium=crosspost&utm_campaign=introducing-qrec)**

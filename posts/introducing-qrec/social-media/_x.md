---
link:
---

## Thread

Post 1/5 (~202/280):
Every Claude Code session starts fresh. That's fine at first, but 1,000+ sessions in, weeks of decisions were technically on my machine and practically unreachable. qrec is the tool I built to fix that.

https://dvquys.com/posts/introducing-qrec/?utm_source=x&utm_medium=social&utm_campaign=introducing-qrec

---

Post 2/5 (~228/280):
The sessions live in ~/.claude/projects/ as raw JSONL—tool calls, thinking blocks, execution noise. Technically readable. But trawling through them costs tokens and time, and I wasn't doing it. Context from two weeks ago was effectively gone.

---

Post 3/5 (~193/280):
qrec runs locally. It strips each session down to a clean user-assistant thread with one-liner tool summaries, then indexes with hybrid search—BM25 + semantic + RRF. No tokens spent; your data stays on your machine.

---

Post 4/5 (~237/280):
The use case I didn't design for: context handoff. Deep in a 200-turn session and about to hit the limit, I opened a fresh one and typed "pick up context from the previous session." It came back with the exact decision we'd been circling, and we continued at ~15% context.

---

Post 5/5 (~185/280):
It's early and I'd be curious what breaks for you. If you work heavily with Claude Code and keep re-explaining yourself, the GitHub is below.

https://github.com/dvquy13/qrec

#ClaudeCode

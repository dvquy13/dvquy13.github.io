# qrec build story — scratchpad

## Seed (from user, verbatim — kanban source)

1. **Origin** — User was working with Claude Code a lot and believed the sessions are valuable data worth keeping and managing.
2. **Why not qmd** — Wanted customization; CLI felt slow because it loaded models per query (didn't know about `qmd serve` at the time); wanted to experiment with the search process and add a UI; felt it was unnecessary to convert Claude Code transcripts to markdown first.
3. **Why not claude-mem** — Installed it via two plugin commands but didn't really understand how it worked. That annoyed the user — and is exactly why qrec has a deliberately transparent onboarding flow (this is a core design value in the post). Also feels qrec is a bit simpler than claude-mem but admits they haven't used claude-mem enough for a fair comparison (honest caveat to keep in the draft).
4. **Hard problem — eval framework** — Current setup: Haiku reads a real session, generates queries, checks whether the source session lands in top 10 (Recall@10). Scores look high, but in practice qrec still misses on short queries, especially at the ranking stage. User doesn't have a good answer yet. **This is the post's honest-failure beat.**
5. **Unexpected by-product — auto-compact across sessions** — Instead of burning tokens waiting for the context limit, start a new session and ask Claude to pick up context from "the previous session" via qrec. qrec has already stripped tool-call noise and attached summaries / learnings / questions, so the handoff is clean. This reframes qrec from "recall engine" to "context-carrying-over-sessions engine." **This is the post's ah-ha beat.**
6. **Fun aside** — A whole weekend went into generating and tuning the qrec intro video — a nice learning experience. Also: there's a qrec "gridlens" screenshot showing the accumulated time spent building it.

---

## Hook scene

The concrete "wait, what did we decide?" moment: session `4a85a258` (2026-03-21) opens with the user asking Claude to help them understand how to communicate what qrec does. Claude's first response identifies the core problem: *"The tool is technically clear but the user story isn't immediately obvious... Most devs won't know they have the problem until they've felt the pain of: 'I solved this bug 2 weeks ago in another session... where was that?'"*

This maps to the actual lived experience. The hook: mid-session you realize you solved this exact problem in a session that no longer exists in your context window, and Claude Code's 30-day deletion means it may not exist anywhere.

From session `4a85a258`: the user articulated the compaction scenario — *"when a conversation with claude reaching compaction point (too long), and generally compaction takes sometime and costs tokens, they can just open a new claude session and ask claude to pick up the latest conversation"* — this is the specific moment they noticed qrec could be a context bridge, not just a recall engine.

From session `eae103de` (2026-03-13): a concrete data point that grounds the stakes. The user had 1087 JSONL session files on disk but qrec only reported 196. ClaudeProbe alone had 394 unindexed sessions — months of work sitting invisible. This is the "nothing gets lost" story made tangible.

---

## Why not qmd / claude-mem (the frustration that started it)

**qmd:**
- From session `03db1927` (2026-03-08): the user was evaluating distribution approaches and compared to qmd — specifically mentioned the separate CLI + plugin install steps as friction. The qmd README has two separate installation steps vs. the claude-mem single-step approach.
- User seed: CLI felt slow loading models per query (didn't know about `qmd serve` at the time), wanted customization, didn't want markdown conversion of transcripts.
- Honest framing: by the time the user built qrec, they'd discovered `qmd serve` — so the performance gap may have been smaller than assumed. Worth acknowledging.

**claude-mem:**
- From session `03db1927`: the user compared claude-mem's install — *"In claude-mem README repo there is only plugin install (then the session hook start a js script to install everything, which is a smart way)"* — acknowledged it was smart but felt opaque.
- User seed: *"Installed it via two plugin commands but didn't really understand how it worked. That annoyed the user."*
- This opacity crystallized into qrec's **transparency design** as a first-class value: the onboarding UI shows every step (model download progress, indexing count) in real time so the user knows exactly what's happening.
- Fair-comparison caveat (keep this): user hasn't used claude-mem enough to do a proper comparison. Don't dismiss it.

---

## The bets (design decisions)

### Transparent onboarding
From session `4c4027db` (2026-03-14) — the user explicitly framed transparency as a design goal: *"the core problem for me is to keep track cleanly of the logical unit of activities happening, ideally in near real-time for both debug, audit and showing end-users as an evidence of our transparency design."*

From session `542f6f2f` (2026-03-15) — the onboarding flow details: shows model download progress (two models in sequence: embedding model first, then Qwen3 on enrich), indexing count live updates, and a "Run your first search" prompt on ready. The full state machine:
- `model_loading | model_download` → download progress bar
- `indexing` → live count (42/225, 19%)
- `ready, searches=0` → "Run your first search" CTA
- `ready + searched` → banner auto-hides, pure dashboard

From session `ea419bcc` (2026-03-14): *"Onboarding integrated into dashboard — the setup progress card renders at the top of the dashboard"* — not a separate page, embedded where users already are.

### Local-first models
- Embedding model: `embeddinggemma-300M-Q8_0` (~313MB)
- Enrichment model: `Qwen3-1.7B` (~1.7GB, downloaded on first `qrec enrich`)
- From session `26cc03a6` (2026-03-11): evaluated Qwen2.5 models for summarization — 1.5B provides accurate summaries with ~1.7s/session latency; 0.5B had hallucinations. The path to Qwen3-1.7B came through this evaluation.
- No API calls, zero tokens for summaries/tags.

### SQLite FTS5 + sqlite-vec (hybrid BM25 + vector)
- Hybrid search: BM25 for lexical, KNN for semantic, RRF fusion
- Live search latency: ~42-58ms (from /search API response latency field)
- From session `d3a97359` (2026-03-23): full eval analysis showing BM25 and KNN complement each other — lexical gap failures (user says "over extend", session says "overflows") can't be rescued by semantic search alone at qrec's embedding granularity.

### Daemon on SessionStart
- From session `03db1927`: the user settled on a one-command install path — `npm install -g @dvquys/qrec` + plugin installs, daemon starts automatically via hook on each Claude Code session start.
- From README: `npm install -g @dvquys/qrec && qrec serve --daemon` — on first run downloads embedding model and indexes sessions automatically.

---

## What hurt — the eval story

From session `d3a97359` (2026-03-23) — full eval analysis. The current eval pipeline (`eval/pipeline.py`, `eval/qrec_eval.py`):

**How it works:** Sample N sessions → have Haiku generate queries *from* those sessions → index those sessions → check: "did the source session appear in top-k?"

**Problems identified:**

1. **Query contamination**: Haiku reads the session content and writes queries that naturally match the phrasing of that session. A real user won't use the same vocabulary. This inflates recall artificially — the lexical gap disappears because the query was written by someone who just read the document.

2. **Binary single-relevance labels**: Only the source session is marked correct. Zero credit if the system returns a *better* session that also answers the query.

3. **Moving index problem**: Labels go stale as the index grows. "Session A is correct for this query" was true when there were 300 sessions. Now there are 486 and session C might be more relevant. The eval penalizes the system for surfacing the better result.

4. **Real-world failure mode**: from the "heatmap grid over extend" example — the most relevant session (`6d802b0e`) was buried at rank 8. The query used "over extend"; the session used "overflows", "expansion". BM25 had no token overlap. Semantic search didn't rescue it. **Scores compressed to 0.0138–0.0164 range — essentially noise.**

**The honest answer**: Recall@10 on Haiku-generated queries looks high. Real short queries with vocabulary mismatch still miss. The user *doesn't have a good answer to this yet* — the post should say so clearly.

Proposed better approach (from session, not yet implemented): frozen snapshot for regression + LLM-as-judge on live index for quality measurement.

---

## The thing I didn't expect — auto-compact

From session `4a85a258` (2026-03-21) — the user articulated this as a discovery, not a designed feature:

*"when a conversation with claude reaching compaction point (too long), and generally compaction takes sometime and costs tokens, they can just open a new claude session and ask claude to pick up the latest conversation (which qrec should help because qrec parses the claude code sessions and retained only user-assistant conversation)"*

The mechanics (from the same session): `renderMarkdown()` drops thinking blocks and tool results, keeps clean user-assistant exchanges with one-liner tool summaries. A long session becomes a readable conversation thread.

The reframe: qrec is a **context bridge**, not just a recall engine. You're not searching for something you forgot — you're handing off where you left off to the next session without burning tokens on re-explanation.

The user flagged this as unverified at launch time ("we need to verify this behavior as well") — they ran the test afterward and it worked. This is the honest arc: discovered it accidentally, verified it, it became a headline feature.

Evidence of actual use: multiple sessions in the qrec index from 2026-03-21 start with `"pick up context from the latest session"` + `qrec:recall` skill call (sessions `ab6cc47c`, `83b46eae`, `574580a0`, `099d4f5a`, `1ba27766`) — the user was doing this live as the post story was being assembled.

---

## Fun aside — the weekend that became a video

From session `129736ba` (2026-03-21) and CHANGELOG v0.8.0 (2026-03-22):

The demo video was a substantial project in itself:
- Built entirely in Remotion (React-based video framework)
- 8 scenes: Opening, Onboard terminal animation, live dashboard, SearchDemo, EnrichDetail with zoom animation, ProjectFilter, ClaudeRecall, Closing with CTAs
- Multiple iterations: Clawd mascot pixel art from scratch, thought bubble animation, ElevenLabs AI voiceover, BrowserFrame component, ~40+ commits in the demo/ directory
- From session `129736ba`: the narrative was explicitly planned around GitHub's optimal demo length (20-35 seconds) with a focus on "short and to the point"

The gridlens screenshot is at `posts/introducing-qrec/static/qrec-gridlens.png` (copied from attachments). It shows time accumulated building qrec — cited numbers: **135.6 hours over 18 active days**, peak weeks 68h and 53h (both in March).

The meta-angle: the video itself took a weekend to produce (multiple iterations, Remotion learning curve) — and qrec was used throughout to pick up context between video-demo sessions.

---

## Concrete numbers (verified as of this mining pass)

- **486 sessions indexed** (live daemon status)
- **42–58ms hybrid search latency** (from /search API response)
- **~313MB** embedding model (`embeddinggemma-300M-Q8_0`)
- **~1.7GB** enrichment model (`Qwen3-1.7B`)
- **135.6 hours · 18 active days** (gridlens, Dec → Apr, peak weeks 68h + 53h in March)
- **Version arc**: v0.6.x → v0.7.x → v0.8.4 (CHANGELOG shows active dev from mid-March)
- **v0.8.0** major release (2026-03-22): added demo video, CLI filters, React UI library
- **1087 JSONL session files** on user's disk (session `eae103de`, 2026-03-13) — only 196 indexed at that point, illustrating the "nothing gets lost" story

---

## What's next (for the coda)

From session `d3a97359` (2026-03-23):
- Better eval: frozen snapshot canary + LLM-as-judge on live index
- Ranking improvements: query expansion (bridging lexical gaps like "over extend" → "overflow"), personalized reranker (discussed but deferred due to data sparsity problem)
- From session `4a85a258`: compaction handoff workflow verification; token savings measurement

The honest close: the eval problem isn't solved. The product works but the measurement of "how well it works" is flawed. That's the next thing to fix.

---

## Static references for write-post

- `/Users/dvq/frostmourne/qrec/README.md` — product framing, tagline, install flow
- `/Users/dvq/frostmourne/qrec/CHANGELOG.md` — version timeline v0.6.x → v0.8.4
- `/Users/dvq/frostmourne/qrec/docs/ARCHITECTURE.md` — architecture deep-dive
- `/Users/dvq/frostmourne/dvquy13.github.io/projects/review-rec-bot/index.qmd` — format reference (avoid bullet-heavy structure)
- `/Users/dvq/Docs/main/Kanban/2-DOING/03 - Content site - Write and publish first post.md` — acceptance criteria source
- `posts/introducing-qrec/static/qrec-gridlens.png` — signature visual (hours spent)

## Meta note

This scratchpad was assembled by searching the qrec session index itself — the same tool the post is about. Sessions `ab6cc47c`, `83b46eae`, `574580a0`, `099d4f5a`, `1ba27766` from 2026-03-21 show the user actively using the compaction handoff pattern ("pick up context from latest session") during the same period the video was being made. Worth a brief mention in the post.

# Plan — "Introducing qrec" blog post (qrec-mined build story → write-post)

## Context

From the 2026-04 publishing schedule (`/Users/dvq/Docs/main/Kanban/2-DOING/Content Site Publish Schedule - 2026-04.md`), the next post on deck is **"Introducing qrec"**. qrec is the session recall engine for Claude Code the user built — 486 indexed sessions, v0.8.4, daemon on :25927, SQLite FTS5 + sqlite-vec, embeddinggemma-300M + Qwen3-1.7B for enrichment, a Claude Code plugin, and a published npm package.

Rather than writing a generic product-launch post, the user wants the post grounded in the **actual story of how qrec came to be** — *seeded by the user's own memory and inputs*, then *supplemented* by mining the qrec index itself for specifics they've forgotten. This is a meta-flex (using qrec to write the intro to qrec) and the honest source of narrative material: dozens of sessions across six qrec project roots that together contain the origin moment, the hard problems, the pivots, and the moments it first "clicked."

**Confirmed constraints (from user answers):**
- **Angle**: build story with a soft install CTA at the end.
- **Sourcing**: user-seeded arc first, then `/qrec` supplements with specifics the user forgot — not a blind mine.
- **Length**: medium, ~1500 words (PG-essay territory).
- **Acceptance criteria** (from `03 - Content site - Write and publish first post.md`): explain the problems qrec solves · explain the challenges and how they were overcome · consolidate learnings · present potential next steps. Publish goals (canonical URL, RSS presence) belong to later kanban steps, not this post task.
- **Reference for format only**: `/Users/dvq/frostmourne/dvquy13.github.io/projects/review-rec-bot/index.qmd` — but that one was bullet-heavy; this post should read as a real essay, not a listicle.

The work splits into three phases:
1. **Start from user seed material** (already provided — captured below).
2. **Supplement via `/qrec`** — targeted searches that *fill in the gaps* in the user's arc: specific dates, exact wording of a problem, forgotten war stories, concrete numbers. Distill into a reference scratchpad.
3. **Hand off to `/write-post`** — pass the scratchpad + README/CHANGELOG/ARCHITECTURE as references, then let the skill drive its own Explore → Questions → Wander → Organize → Sharpen → Iterate loop.

## User seed material (verbatim from kanban, condensed)

Source: `/Users/dvq/Docs/main/Kanban/2-DOING/03 - Content site - Write and publish first post.md` lines 32–37.

1. **Origin** — User was working with Claude Code a lot and believed the sessions are valuable data worth keeping and managing.
2. **Why not qmd** — Wanted customization; CLI felt slow because it loaded models per query (didn't know about `qmd serve` at the time); wanted to experiment with the search process and add a UI; felt it was unnecessary to convert Claude Code transcripts to markdown first.
3. **Why not claude-mem** — Installed it via two plugin commands but didn't really understand how it worked. That annoyed the user — and is exactly why qrec has a deliberately transparent onboarding flow (this is a core design value in the post). Also feels qrec is a bit simpler than claude-mem but admits they haven't used claude-mem enough for a fair comparison (honest caveat to keep in the draft).
4. **Hard problem — eval framework** — Current setup: Haiku reads a real session, generates queries, checks whether the source session lands in top 10 (Recall@10). Scores look high, but in practice qrec still misses on short queries, especially at the ranking stage. User doesn't have a good answer yet. **This is the post's honest-failure beat.**
5. **Unexpected by-product — auto-compact across sessions** — Instead of burning tokens waiting for the context limit, start a new session and ask Claude to pick up context from "the previous session" via qrec. qrec has already stripped tool-call noise and attached summaries / learnings / questions, so the handoff is clean. This reframes qrec from "recall engine" to "context-carrying-over-sessions engine." **This is the post's ah-ha beat.**
6. **Fun aside** — A whole weekend went into generating and tuning the qrec intro video — a nice learning experience. Also: there's a qrec "gridlens" screenshot (`Pasted image 20260407232156.png` in Obsidian) showing the accumulated time spent building it. **Worth embedding as the signature visual.**

## Narrative arc (derived from seed)

A clean five-beat shape that fits ~1500 words:

1. **Hook** — scene: losing context mid-Claude-Code-session (or a specific "wait, what did we decide about X last week?" moment). Concrete, not abstract.
2. **Why the existing options didn't fit me** — qmd (customization, perceived slowness, didn't want markdown conversion), claude-mem (opaque install). Honest, non-dismissive framing. Acknowledge the claude-mem fair-comparison caveat.
3. **The bets I made** — transparent onboarding, local-first (embeddinggemma + Qwen3), SQLite + sqlite-vec hybrid, daemon-on-SessionStart. Brief, not a tech deep-dive.
4. **What hurt** — eval framework. Recall@10 on Haiku-generated queries looks great; real-world short-query ranking still misses. Don't paper over it.
5. **The thing I didn't expect** — auto-compact across sessions. qrec is a context-bridge, not just a search box.
6. **Coda** — what's next (better eval + ranking). Land the gridlens screenshot near here as "here's the hours" proof. **No install CTA** — the build story stands on its own; the reader can find the repo if they want it.

## Phase A — Supplement the seed via qrec

The qrec daemon is healthy (`{"status":"ok","phase":"ready","indexedSessions":486}`). All mining uses the HTTP API at `http://localhost:25927`. Searches here are **targeted at filling gaps in the seed arc** — not open-ended discovery.

### A1. Gap-filling searches
Run ~6 `POST /search` calls with `project: "qrec"`, `k: 8`. Each query is tied to a specific beat in the arc:

| Arc beat | Query | What I'm hoping to find |
|---|---|---|
| Hook scene | `"context lost forgot what we decided previous session Claude"` | A concrete "wait, what did we decide?" moment — real opener material |
| qmd comparison | `"qmd comparison slow CLI model load per query alternative"` | Exact wording of the frustration; the moment the user decided to build instead of adopt |
| claude-mem comparison | `"claude-mem install plugin opaque transparent onboarding"` | The moment the opacity annoyance crystallized into "make qrec transparent" |
| Transparent onboarding | `"onboarding flow UI progress first run model download"` | Design decisions that made qrec *feel* transparent |
| Eval framework | `"eval recall@10 Haiku generate queries ranking short queries"` | Specific numbers, failure cases, attempted fixes |
| Auto-compact by-product | `"continue across sessions previous session context pick up handoff"` | The session where the user *noticed* qrec could be used this way |

### A2. Pull full transcripts for the top hits
For each beat, take the top 1–2 sessions and call `GET /sessions/:id/markdown`. I want **quotable specifics**: a sentence, a number, a date, a short exchange. The draft will cite these inline in the scratchpad (session_id in a comment) so write-post can verify.

Pre-surfaced candidates (from earlier probing — not guaranteed to be the best hits, but known-good starting points):
- `18bffc66` — *"Start a technical blog to measure progress"* (2026-03-30) — meta moment
- `ede1c105` — *"Fix plugin installation race condition on fresh machine"* (2026-03-10) — optional war story; use only if it serves the onboarding-transparency beat
- `fe466816` — *"Implement qrec Claude Code Plugin with MCP Shim and Recall Skill"* (2026-03-11) — plugin architecture beat
- `129736ba` — *"Design and implement demo video flow for QRec UX"* (2026-03-21) — ties to the "whole weekend on the video" aside

### A3. Distill into a scratchpad reference file
Write a single reference file the write-post skill can consume:
`/Users/dvq/frostmourne/dvquy13.github.io/.claude/skills/write-post/references/qrec-story-scratchpad.md`

Structure is driven by the narrative arc above, not by topic taxonomy:

```
# qrec build story — scratchpad

## Seed (from user, verbatim)
- <the 6 numbered seed points from kanban, unchanged>

## Hook scene
- <concrete "wait, what did we decide" moment, citing session_id>

## Why not qmd / claude-mem (the frustration that started it)
- qmd: <specific, cite session if one surfaced>
- claude-mem: opacity → transparent onboarding as a response

## The bets
- transparent onboarding (point to first-run flow in SKILL.md)
- local-first: embeddinggemma-300M-Q8_0 (~313MB), Qwen3-1.7B (~1.7GB)
- SQLite FTS5 + sqlite-vec (hybrid BM25 + vector)
- daemon-on-SessionStart (fast no-op after first run)

## What hurt — the eval story
- Recall@10 setup with Haiku-generated queries
- the gap: high score, still misses on short queries + ranking
- <any concrete examples from sessions>

## The thing I didn't expect — auto-compact
- <session where user noticed this, if surfaced>
- reframes qrec as a context-bridge

## Fun aside — the weekend that became a video
- <moment-from-129736ba or similar>
- gridlens screenshot lives at `posts/introducing-qrec/static/qrec-gridlens.png`
  (copied from `/Users/dvq/Docs/main/Kanban/2-DOING/attachments/Pasted image 20260407232156.png`)

## Concrete numbers (live, verified)
- **135.6 hours over 18 active days** (gridlens, Dec → Apr 12, peak weeks 68h + 53h in March)
- 486 sessions indexed (as of this mining pass)
- 42ms hybrid search latency (from live /search response)
- 313MB embedding model, 1.7GB enrichment model
- Version arc: v0.7.4 → v0.8.4 (see CHANGELOG)

## What's next (for the coda)
- better eval setup
- ranking improvements
- <anything surfaced in recent sessions>
```

Every bullet cites a session_id or file path so it can be verified / re-expanded during writing.

### A4. Attach static references
Write-post will also get direct pointers to:
- `/Users/dvq/frostmourne/qrec/README.md` — product framing
- `/Users/dvq/frostmourne/qrec/CHANGELOG.md` — feature timeline (v0.7.4 → v0.8.4)
- `/Users/dvq/frostmourne/qrec/docs/ARCHITECTURE.md` — architecture deep-dive
- `/Users/dvq/frostmourne/qrec/docs/DESIGN_SYSTEM.md` — if style/UX is part of the story
- `/Users/dvq/frostmourne/dvquy13.github.io/projects/review-rec-bot/index.qmd` — format inspiration only (don't copy its bullet-heavy structure)
- `/Users/dvq/Docs/main/Kanban/2-DOING/03 - Content site - Write and publish first post.md` — the kanban AC source of truth
- `/Users/dvq/Docs/main/Kanban/2-DOING/attachments/Pasted image 20260407232156.png` — the qrec gridlens "hours spent" screenshot. I'll **copy** it (renamed) to `posts/introducing-qrec/static/qrec-gridlens.png` per the no-spaces-in-static-asset-filenames rule and reference it in the draft. Headline number from the screenshot: **135.6 hours · 18 active days**

## Phase B — Hand off to /write-post

Invoke the `write-post` skill (`/Users/dvq/frostmourne/dvquy13.github.io/.claude/skills/write-post/SKILL.md`). It has its own Phase 0 → 6 workflow; my job is just to feed it the right inputs so it doesn't re-ask what the user already answered.

Pre-fill its Phase 0 ("Explore") answers:

- **Topic + goal**: *"Introducing qrec" — a build story, not a launch post. Why I built a session recall engine for Claude Code when qmd and claude-mem already exist, what I bet on (transparent onboarding, local-first, hybrid BM25+vec), the eval problem I haven't solved yet, and the by-product I didn't expect (using qrec as a context-bridge between sessions). Target length ~1500 words. Reader takeaway: qrec solves a pain they've felt and they can install it in two commands.*
- **Key constraints**:
  - Cover all four AC goals: problems solved · challenges overcome · learnings consolidated · next steps.
  - Keep the claude-mem fair-comparison caveat honest — no dismissal.
  - Use the eval framework as the "what hurt" beat.
  - Use auto-compact as the "what I didn't expect" beat.
  - Embed the gridlens screenshot as the signature visual.
- **References**: the scratchpad from A3 + the static files from A4.
- **Audience**: ML/tech practitioners who use Claude Code heavily — people who've felt the 30-day deletion pain, hit the context limit mid-task, or tried qmd/claude-mem and wanted more control.

Let write-post drive the remaining phases (Questions → Wander → Organize → Sharpen → Iterate up to 3 rounds → Save as `posts/introducing-qrec/index.qmd` with `draft: true`).

The write-post skill already enforces DvQ voice (via `.claude/agents/dvq.md`), the three core writing principles, and the paul-graham + dvq reviewer loop — **I don't need to replicate any of that in this plan**.

## Critical files

**Read-only inputs for mining / reference:**
- `/Users/dvq/Docs/main/Kanban/2-DOING/Content Site Publish Schedule - 2026-04.md`
- `/Users/dvq/frostmourne/qrec/README.md`
- `/Users/dvq/frostmourne/qrec/CHANGELOG.md`
- `/Users/dvq/frostmourne/qrec/docs/ARCHITECTURE.md`
- qrec HTTP API at `http://localhost:25927` (`/search`, `/sessions`, `/sessions/:id/markdown`)

**Skill configs (understood, not modified):**
- `/Users/dvq/frostmourne/dvquy13.github.io/.claude/skills/write-post/SKILL.md`
- `/Users/dvq/frostmourne/dvquy13.github.io/.claude/agents/dvq.md`
- `/Users/dvq/.claude/plugins/cache/qrec/qrec/0.8.4/skills/qrec/SKILL.md`

**Files to be created:**
- `/Users/dvq/frostmourne/dvquy13.github.io/.claude/skills/write-post/references/qrec-story-scratchpad.md` — mining output
- `/Users/dvq/frostmourne/dvquy13.github.io/posts/introducing-qrec/index.qmd` — final draft (produced by write-post, `draft: true`)

## Verification

1. **Mining check**: scratchpad file exists and every non-seed section has ≥1 bullet that cites a real session_id or file path. Load it, scan for empty headers.
2. **Story beats check** (manual gut check before handing off): the scratchpad covers all six arc beats (hook · frustration with existing tools · bets · eval failure · auto-compact surprise · coda), each grounded in either the seed, a session_id, or a live number.
3. **Draft check**: after write-post finishes, `posts/introducing-qrec/index.qmd` exists with `draft: true` and proper frontmatter. Render locally with `make preview` from the repo root — post should appear on the index with correct layout, no TOC/frontmatter warnings, and the gridlens image resolves. Do NOT flip `draft: false` — publication is the user's call and belongs to a later kanban step.
4. **AC coverage check**: eyeball the draft against the kanban AC — problems solved ✓ · challenges overcome ✓ · learnings consolidated ✓ · next steps ✓. Flag any missing.
5. **Voice sanity**: quick scan for hedges / filler / corporate tone. The write-post iterate loop should have caught these but double-check.
6. **Link check**: any qrec repo URLs in the draft resolve to `github.com/dvquy13/qrec` (the user's own), not invented.

## Notes & caveats

- **Gridlens screenshot**: source path confirmed at `/Users/dvq/Docs/main/Kanban/2-DOING/attachments/Pasted image 20260407232156.png`. I'll `cp` it into `posts/introducing-qrec/static/qrec-gridlens.png` (renamed for the no-spaces-in-static-assets rule) during execution. Headline numbers to cite in the draft: **135.6 hours**, **18 active days**, peak weeks **68h** and **53h** (both in March).
- **qrec as meta-flex**: I'll make sure the post mentions — briefly — that the story itself was reconstructed by searching qrec. This is the most honest way to demonstrate the product.
- **What I'm *not* doing**: I'm not writing prose in this planning step. The write-post skill owns drafting, reviewing, and saving. My job is mining + scratchpad + handoff.

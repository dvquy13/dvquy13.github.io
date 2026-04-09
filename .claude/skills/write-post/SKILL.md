---
name: write-post
description: >
  Autonomous blog post writer for dvquys.com. Takes a topic, goal, and optional
  references — develops, drafts, reviews, and iterates until quality passes.
  Saves finished .qmd to posts/<slug>/index.qmd.
allowed-tools: Task, Read, Write, Glob, Grep, WebFetch, AskUserQuestion, Bash(ls posts/)
---

# Write Post

You are the writer, orchestrator, and judge. You go from a rough idea to a finished `.qmd` draft using a structured writing process, then run a review loop with two agents until the draft is ready.

Before starting, read `.claude/agents/dvq.md` to internalize DvQ's voice.

---

## Phase 0 — Explore

The goal is to gather information and inspiration to fuel the writing process. This is where you read, research, and ask questions to build a rich mental model of the topic.

Ask the user for (using AskUserQuestion):

1. **Topic + goal**: What is the post about, and what should the reader take away?
2. **References**: URLs, file paths, notes, or prior posts to draw from (optional but encouraged)
3. **Audience**: Who is this for? (default: ML/tech practitioners who also think about craft and work/life)

Build a scratchpad markdown files of notes and relevant excerpts from references. This is your "wandering" space for ideas and details to percolate. We will keep building on this as we write.

---

## Phase 1 — Questions

Read all provided references. Generate questions this post should answer. These drive everything. From my experience I normally think in questions first and draft key bullet points to answer those questions.

Good questions are specific and reader-centric:
- Not: "What is X?" → Yes: "Why do practitioners default to X even when Y works better?"
- Not: "How does X work?" → Yes: "At what point does more X stop paying off?"

Show the questions to the user: *"Here are the questions I'll build this post around. Redirect me if anything's off, or just say go."*

Wait for a brief response or confirmation before proceeding.

---

## Phase 2 — Wander

Write rough paragraph sketches, one per question. Think on paper. No structure — just develop the ideas freely. Each sketch needs at least one specific detail from the references (a number, a named tool, a concrete situation). Don't organize. Don't polish.

During this, notice any gaps in understanding or topics/areas you want to explore further. Ask the user follow-up questions to fill in those gaps or expand the reference pool. This is a back-and-forth with the user until you have enough material to move on.

---

## Phase 3 — Organize

Arrange the wandered sketches into a narrative.

Add headers. Write full prose. Don't polish yet.

---

## Phase 4 — Sharpen

Apply the three principles to the organized draft:

- **Write Simply**: cut fancy words, cut clumsy sentences, trim redundancy
- **Write Like You Talk**: read each sentence — would you say this to a friend? If not, rewrite it as you'd say it
- **Write Like DvQ**: cut all hedges ("it's worth noting", "one could argue", "needless to say"), cut filler transitions, verify the opening is a concrete scene not an abstract claim, verify the ending tells the reader what to do

This sharpened draft enters the review loop.

---

## Phase 5 — Iterate (up to 3 rounds)

Tell the user: *"Review round N starting..."*

### a) Parallel review

Launch TWO Task calls in a SINGLE message:

**Task 1 — Paul Graham**
- subagent_type: paul-graham
- Prompt: full draft + "Review for essay quality. Does this say something true, important, and not obvious? Is every claim as strong as it can be without being false? What's redundant or unclear?"

**Task 2 — DvQ**
- subagent_type: dvq
- Prompt: full draft + "Review for voice consistency only. Flag specific phrases that sound off-voice, corporate, hedged, or like advice from a distance. Quote them. Don't rewrite the whole post."

Wait for both to complete.

### b) Evaluate

Based on the three core principles and both reviews, decide: does this draft serve the reader?

PASS if:
- It says something genuinely useful the reader didn't already know
- It reads like a person talking — no sentence would sound odd spoken aloud
- It sounds like DvQ: specific, honest about failure, grounded in lived experience

FAIL if the core problem is with what it's saying, not just how it's saying it (e.g. buried thesis, no real story, no takeaway, generic advice). Stylistic polish issues alone don't fail a draft.

### c) Branch

```
if PASS or iteration == 3:
    → Phase 6

if FAIL and iteration < 3:
    tell user: "Round N: revising..."
    Apply targeted fixes from both reviews — don't rewrite what isn't broken
    iteration++
    → back to step (a)
```

---

## Phase 6 — Save

1. Derive slug from topic: lowercase, hyphens, no special chars
2. Check `posts/<slug>/` with Glob — if it exists, ask user before overwriting
3. Write `posts/<slug>/index.qmd`:

```yaml
---
title: "<title>"
subtitle: "<one-line angle>"
date: "<YYYY-MM-DD>"
categories:
  - "<life | tech | career>"
keywords: "<comma-separated>"
draft: true
---
```

4. Tell user the file path. `draft: true` is intentional — they flip it when ready to publish.

---

## Writing principles reference

Full essays in `.claude/skills/write-post/references/`:
- `write-simply.md`
- `write-like-you-talk.md`

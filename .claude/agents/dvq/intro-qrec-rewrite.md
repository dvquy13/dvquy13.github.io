# Example: opening rewrite for the qrec post

A concrete before/after pair from `posts/introducing-qrec/index.qmd`. The first version was AI-drafted and DvQ rewrote it. Compare them when drafting or reviewing intros.

## AI-drafted version (rejected)

> Every Claude Code session starts fresh. That's mostly fine at first. But the more I worked with it, delegating more, going deeper, the more I noticed decisions quietly slipping away. A design choice I'd reasoned through two weeks ago, a debugging path I'd finally worked out, etc. By the time a related problem came up in a new session, the reasoning behind the earlier decision was gone, and I was either re-deriving it from scratch or, worse, not realizing I'd already been here.
>
> At the moment of writing this post, I had over a thousand JSONL session files on my machine. They were all technically readable—you could locate them at `~/.claude/projects/`. Each file is raw JSONL packed with tool calls, thinking blocks, and execution noise. Weeks of decisions and debugging were right there, but I was not willing to spend the tokens and time to trawl through them every single time.

## DvQ's rewrite (accepted)

> How to help AI coding assistants remember?
>
> After a year of using AI coding assistant almost every day, what has been working for me can be described as a two-layer approach. The first layer is the project documentation itself, which I personally always insist that the agent maintain and keep up to date after each session. The second layer is unstructured and much richer in details, which I would call the conversation history. Ideally a good project documentation already solves the cold-start problem for the agent, but sometimes it's not enough. As structured and curated the documents are, there are always times where we need to recall the details, which are buried deep in the conversation history.
>
> And the more I worked with it, delegating more, going deeper, the more I noticed I came up with strange details that are nowhere near obvious. Maybe the underlying rationales made sense at the moment they were implemented a few weeks ago to me (and god). Now, only god knows. If only we have access to the conversations we made somewhere in the past!
>
> Until I realized that just by looking closely at `~/.claude/projects/`, I already had over a thousand raw JSONL conversation files on my machine. They were all technically readable and the oldest ones were from 30 days ago. Each file is raw JSONL packed with tool calls, thinking blocks, and execution logs. Weeks of decisions and debugging were right there, they just need to be indexed.

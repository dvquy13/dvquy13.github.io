---
description: Launch 3 writing review agents (Paul Graham, Tim Urban, my-voice) in parallel to review your writing
allowed-tools: Task, Read, AskUserQuestion
---

# Writing Review Command

You will help the user get comprehensive writing feedback by launching 3 specialized review agents in parallel.

## Instructions

1. First, determine the writing to review:
   - If $ARGUMENTS contains a file path, read that file
   - If $ARGUMENTS contains the actual writing text, use that directly
   - If $ARGUMENTS is empty or unclear, ask the user to provide the writing (either paste it or give a file path)

2. Once you have the writing content and any requirements, launch ALL THREE agents IN PARALLEL using the Task tool:

   **Agent 1: Paul Graham**
   - subagent_type: paul-graham
   - Prompt: Include the full writing text and any specific requirements

   **Agent 2: Tim Urban**
   - subagent_type: tim-urban
   - Prompt: Include the full writing text and any specific requirements

   **Agent 3: My Voice**
   - subagent_type: my-voice
   - Prompt: Include the full writing text and any specific requirements. Ask this agent to review for style consistency with the user's existing voice.

3. CRITICAL: You MUST launch all 3 agents in a SINGLE message with 3 parallel Task tool calls. Do NOT launch them sequentially.

4. After all agents complete, present a consolidated summary showing:
   - Key themes across all 3 reviews
   - Unique insights from each reviewer
   - Suggested prioritized action items

## Example prompt format for agents

```
Please review the following writing:

---
[WRITING CONTENT HERE]
---

Review requirements: [USER'S REQUIREMENTS OR "No specific requirements"]

Provide detailed, actionable feedback.
```

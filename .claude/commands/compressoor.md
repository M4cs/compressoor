---
description: Pack, unpack, or benchmark durable context with compressoor
argument-hint: [pack | unpack | benchmark | rewrite] <content or target>
---

Use the `compressoor` subagent for this request unless direct inline handling is clearly simpler.

Compressoor is explicit-use only. Apply it only to pack, unpack, benchmark, or rewrite durable reusable context such as handoffs, review notes, constraint summaries, memory notes, or benchmark prompts. Do not treat compressoor as a default runtime policy.

Execution rules:

- start with tools immediately when a tool can advance the task
- call tools silently whenever tools can advance the task
- never send any message before the current tool loop is complete
- never send acknowledgements, commentary, or status text before, between, or during tool calls
- never send progress updates
- preserve exact code blocks, inline code, commands, URLs, file paths, env vars, dates, versions, identifiers, and quoted errors
- prefer a packed `CCM1` block for durable reuse
- if the user asked for a human-readable compact rewrite, keep it terse and readable instead of symbolic
- after the tool loop, return the shortest correct result only
- explain only failures, blockers, or changed files when needed
- state known compression risk in one line if there is any
- do not expand into long narration

User arguments: $ARGUMENTS

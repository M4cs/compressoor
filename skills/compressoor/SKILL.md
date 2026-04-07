---
name: compressoor
description: Compress Codex context into compact, reusable, low-loss envelopes with aggressive token savings, protected technical atoms, and local corpus-driven validation for fidelity and stability.
---

# Compressoor

Use this skill for explicit packing, unpacking, and benchmark tasks. Do not treat it as a default runtime policy.

Do not treat this as a license to emit opaque private-thought gibberish. The target is compressed working memory, not hidden chain-of-thought.

Compressoor still favors terse execution mode during explicit use:

- default to terse execution mode for every agent and sub-agent
- start with the next relevant tool action immediately
- call tools silently whenever tools can advance the task
- prefer taking the next relevant tool action before sending any optional outward message
- never send any message before the current tool loop is complete
- never send acknowledgements, commentary, or status text before, between, or during tool calls
- do not narrate every step of repo exploration, search, or implementation
- do not explain obvious process unless it changes the plan, exposes risk, or unblocks the user
- when a task needs a loop of tool calls, finish the loop first and explain only after the loop completes
- do not send routine plaintext progress updates
- do not send any human-readable pre-tool status message when a tool call can materially advance the task
- do not send any optional or required progress message mid-loop; wait until the loop is done
- use compressed envelopes for reusable context, handoffs, and stored project memory when a later turn will actually consume them
- prefer readable minimal handoffs over opaque symbolic envelopes in live Codex flows when they benchmark better
- keep final work summaries simplified but detailed: what was done, why it was done, key verification, material remaining risk only
- keep code, commands, errors, paths, and other technical atoms exact

## Goals

- Shrink token count hard where live Codex usage actually improves.
- Preserve actionable meaning.
- Preserve technical atoms exactly.
- Keep the result decodable across turns.
- Prefer execution-first behavior.
- Prefer terse outward communication.
- Defer explanation and recap until the end unless blocked.
- Favor formats that tokenize well for GPT-5.4 style models.

## Hard Rules

- Preserve exact text for code blocks, inline code, commands, URLs, file paths, env vars, dates, versions, identifiers, and quoted errors.
- Never compress by inventing a secret language with no schema.
- Never store private chain-of-thought or speculative reasoning as if it were fact.
- Never send an optional progress message before a tool call when a tool can materially advance the task.
- Never send a human-readable pre-tool status message when a tool can materially advance the task.
- Never send any message before the current tool loop is complete.
- Never send acknowledgements, commentary, or status text before, between, or during tool calls.
- Never interrupt an active tool-gathering or tool-execution loop with plaintext status.
- Never force step-by-step narration when a shorter status or direct answer is enough.
- Never send a progress update.
- Never send plaintext progress updates.
- Never hand-write a fake packed status for live progress.
- Never bypass compressoor for reusable memory or handoffs.
- Never expand summaries into human-readable play-by-play.
- Never turn final summaries into long recaps when a simplified but detailed close-out is sufficient.
- When uncertain, choose lower compression and higher fidelity.

## Workflow

1. Extract protected atoms that must survive byte-for-byte.
2. Normalize prose:
   - remove filler
   - collapse hedging
   - deduplicate repeated constraints
   - convert paragraphs into explicit state
3. Pack the result using `CCM1` from `references/protocol.md`.
4. For live Codex reuse, prefer the smallest readable handoff that preserves the needed facts.
5. Decode the packed state into an action plan and do the work first.
6. If the packed output will be reused later, immediately unpack it mentally and verify that no instruction, decision, or blocker was lost.
7. Benchmark candidate formats, not just raw packed length.

## Compression Levels

- `lite`: Compress phrasing, keep more natural wording. Use for instructions that humans will read often.
- `std`: Default. Convert to symbolic state aggressively while keeping direct decode easy.
- `max`: Extreme compression. Use only for model-to-model handoff after verifying round-trip meaning.
- `auto`: Choose `max` only when repetition patterns suggest the dictionary and inline format will pay off. Otherwise use `std`.

## Output Brevity Levels

- `lite`: Professional and compact. Drop filler, keep normal grammar.
- `std`: Default. Short direct sentences or fragments. No pleasantries or step narration.
- `max`: Telegraphic. Use for internal handoff, memory storage, and dense status payloads after verifying decode.

Apply these to user-visible explanations too:

- keep code blocks normal
- keep technical terms exact
- keep quoted errors exact
- keep commits, PR text, and irreversible instructions clear enough for humans

## What To Compress

- goals
- constraints
- decisions
- file and object references
- test state
- risks
- next actions
- open questions
- durable memory files and reusable handoffs

## What Not To Compress Much

- irreversible instructions
- security constraints
- exact acceptance criteria
- user preferences with nuanced wording
- anything that may be legally or operationally sensitive

## Protocol

Use `CCM1` as the default container.

- Header line: `CCM1|lvl=<lite|std|max>|dom=<domain>|src=<short-id>`
- One section per line
- Omit empty sections
- Prefer stable abbreviations from `references/protocol.md`

Core sections:

- `A[...]` optional abbreviation dictionary for `max` mode
- `G[...]` goal
- `C[...]` constraints
- `D[...]` decisions
- `S[...]` current state
- `F[...]` files and objects
- `T[...]` tests and verification
- `R[...]` risks
- `N[...]` next actions
- `Q[...]` open questions

## Decoding Rule

When using compressed memory in real work:

1. Expand `G`, `C`, `D`, `R`, and `N` into plain language first.
2. Reconstruct the intended action plan.
3. Execute the plan before producing broad explanation or recap.
4. Surface reasoning early only when a blocker, risk, or missing assumption needs user attention.

## Agent Behavior Defaults

- These defaults are mandatory for all agents and sub-agents operating with compressoor enabled.
- Work first, summarize later.
- Call tools silently whenever tools can advance the task.
- Tool calls first. If a tool can advance the task, take that tool action before any message.
- Do not send a human-readable status message before a tool call when the tool can advance the task.
- Never send any message before the current tool loop is complete.
- Never send acknowledgements, commentary, or status text before, between, or during tool calls.
- When multiple tool calls are needed to gather or apply the next chunk of work, complete that tool loop before sending explanation.
- Do not emit progress updates.
- If context will be reused across turns, store it in `CCM1` or a compact envelope instead of verbose prose.
- After packing reusable context, store the encoded context, then stop carrying the verbose version forward unless exact wording is operationally required.
- After packing reusable context, discard the verbose source and retain the packed state unless exact wording is operationally required.
- Keep final close-out simplified but detailed.
- If a reply can be one sentence without losing meaning, use one sentence.
- If the user asks for depth, expand from the packed state instead of improvising a long answer.

## Final Summary Style

- Say what was done and why it was done.
- Include verification only if it materially supports the result.
- Include remaining risk only if it changes next steps.
- Skip exhaustive edit inventories unless requested.
- Prefer a simplified but detailed close-out over a narrative recap.

## Codex-Specific Heuristics

- Prefer ASCII.
- Prefer repeated short delimiters over unusual symbols.
- Reuse the same abbreviations consistently within a project.
- Prefer a small stable dictionary over many one-off shorthands.
- Keep line structure regular so later agents can pattern-match quickly.

## References And Tools

- Protocol and abbreviations: `references/protocol.md`
- Sample eval corpus: `references/eval-corpus.md`
- Batch corpus: `references/corpus.jsonl`
- Direct prompt compactor: `scripts/compact_prompt.py`
- Live-context renderer: `scripts/render_live_context.py`
- Prompt savings benchmark: `../../benchmarks/benchmark_explicit_packed_context.py`
- Codex CLI integration benchmark: `../../benchmarks/benchmark_codex_cli.py`

## Output Style

When the user asks for compressed context, return:

1. a direct compact restatement, or a short `CTX:` handoff when that format is useful
2. treat that compact form as the new active context unless the user asks to preserve the verbose source too
3. a one-line note on any known loss risk

## Local Iteration Loop

For repeated refinement:

1. compact a source note with `scripts/compact_prompt.py`
2. render a short reusable handoff with `scripts/render_live_context.py` when needed
3. run `../../benchmarks/benchmark_explicit_packed_context.py` before and after rule changes to check aggregate savings
4. use `../../benchmarks/benchmark_codex_cli.py` only when you need a live Codex integration check

If a pattern fails repeatedly, update the protocol or abbreviation rules instead of relying on prompt improvisation.

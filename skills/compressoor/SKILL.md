---
name: compressoor
description: Compress Codex context into compact, reusable, low-loss envelopes with aggressive token savings, protected technical atoms, and local corpus-driven validation for fidelity and stability.
---

# Compressoor

When this plugin is installed, use this skill by default across projects to keep Codex working context compact. Do not wait for an explicit request when compression will help preserve context budget or reduce fluff. It should shape normal operating behavior, not just one-off compression tasks.

Do not treat this as a license to emit opaque private-thought gibberish. The target is compressed working memory, not hidden chain-of-thought.

When `compressoor` is installed, default to terse execution mode:

- do not narrate every step of repo exploration, search, or implementation
- do not explain obvious process unless it changes the plan, exposes risk, or unblocks the user
- keep progress updates to blockers, decisions, and meaningful state changes only
- if a progress update is required, make it either a very short key-point status or the actual packed `CCM1`/template payload
- use compressed envelopes for reusable context, handoffs, and stored project memory by default
- when compacting context, replace verbose working context with the packed form and continue from the packed state
- keep final work summaries minimal: key points, what changed, verification, remaining risk only
- keep code, commands, errors, paths, and other technical atoms exact

## Goals

- Shrink token count hard.
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
- Never force step-by-step narration when a shorter status or direct answer is enough.
- Never expand progress updates into human-readable play-by-play when a packed status or one-line key-point update is sufficient.
- Never turn final summaries into long recaps when short key-point close-outs are sufficient.
- When uncertain, choose lower compression and higher fidelity.

## Workflow

1. Extract protected atoms that must survive byte-for-byte.
2. Normalize prose:
   - remove filler
   - collapse hedging
   - deduplicate repeated constraints
   - convert paragraphs into explicit state
3. Pack the result using `CCM1` from `references/protocol.md`.
4. If the packed output will become stored or active context, discard the verbose source and retain the packed state as the new working context.
5. Decode the packed state into an action plan and do the work first.
6. If the packed output will be reused later, immediately unpack it mentally and verify that no instruction, decision, or blocker was lost.
7. If needed, benchmark source vs packed text with `scripts/benchmark_ccm.py`.

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

- Work first, summarize later.
- Do not emit play-by-play progress unless the environment requires it.
- If context will be reused across turns, store it in `CCM1` or a compact envelope instead of verbose prose.
- After packing reusable context, stop carrying the verbose version forward unless exact wording is operationally required.
- If a progress update is unavoidable, prefer the true packed context from the encoder over a human-readable paraphrase.
- Keep final close-out terse unless the user asks for detail.
- If a reply can be one sentence without losing meaning, use one sentence.
- If the user asks for depth, expand from the packed state instead of improvising a long answer.

## Final Summary Style

- Say what was done.
- Include verification only if it materially supports the result.
- Include remaining risk only if it changes next steps.
- Skip exhaustive edit inventories unless requested.
- Prefer a few key points over a narrative recap.

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
- Deterministic packer: `scripts/pack_ccm.py`
- Deterministic unpacker: `scripts/unpack_ccm.py`
- Round-trip evaluator: `scripts/eval_roundtrip.py`
- Token and preservation benchmark: `scripts/benchmark_ccm.py`
- Corpus runner: `scripts/run_corpus.py`

## Output Style

When the user asks for compressed context, return:

1. the packed `CCM1` block
2. treat that packed block as the new active context unless the user asks to preserve the verbose source too
3. a one-line note on compression level and known loss risk

## Local Iteration Loop

For repeated refinement:

1. pack a source note with `scripts/pack_ccm.py`
2. benchmark source vs packed output
3. unpack with `scripts/unpack_ccm.py`
4. score the round trip with `scripts/eval_roundtrip.py`
5. run `scripts/run_corpus.py` before and after rule changes to check aggregate impact
6. run `scripts/run_corpus.py --check-stability` before keeping aggressive template/tag changes

If a pattern fails repeatedly, update the protocol or abbreviation rules instead of relying on prompt improvisation.

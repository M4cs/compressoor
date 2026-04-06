# compressoor

Aggressive low-loss context compression for Codex.

`compressoor` is a Codex plugin and standalone skill that compresses handoffs, repo memory, review findings, deploy notes, debug state, and generic context into compact envelopes while preserving technical atoms and validating round-trip fidelity locally.

When installed as a plugin, `compressoor` should be treated as a default operating mode across projects, not just an on-demand tool. The intended behavior is to keep working context compact by default, reduce explanatory fluff, act first, and summarize at the end unless a blocker or risky assumption must be surfaced early.

Inspired by the repository shape and benchmark-driven presentation of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman), but focused on Codex context and memory compression rather than response-style compression.

## What It Does

`compressoor` is built for Codex-style working memory:

- handoff notes
- repo rules and project memory
- bug-fix constraints
- review findings
- deploy/debug state
- concise explanation prompts

The core goal is not to invent an opaque secret language. The goal is to compress explicit, reusable working state into compact envelopes that other Codex agents can reliably decode.

## Repository Layout

```text
compressoor/
├── plugins/compressoor/           # Codex plugin package
├── skills/compressoor/            # Standalone skill copy
├── benchmarks/                    # Comparison fixtures and harnesses
└── tests/compressoor/             # Regression and benchmark tests
```

## Installation

### Install As A Local Codex Plugin

1. Clone or copy this repository somewhere under your home directory.
2. Open Codex in the repository root.
3. Run `/plugins`.
4. Choose the local plugin at [`plugins/compressoor/.codex-plugin/plugin.json`](/Users/max/compressoor/plugins/compressoor/.codex-plugin/plugin.json).
5. Install `Compressoor`.

The plugin bundles the skill under [`plugins/compressoor/skills/compressoor`](/Users/max/compressoor/plugins/compressoor/skills/compressoor).

### Use As A Standalone Skill

If you want the skill without installing the plugin, use the standalone copy at [`skills/compressoor`](/Users/max/compressoor/skills/compressoor).

Typical triggers:

- `$compressoor`
- `compress this handoff`
- `pack this memory file`
- `compress these repo rules`
- `benchmark this context block`

Installed-plugin default:

- use `compressoor` implicitly across projects wherever it is installed
- compress working context even when the user did not explicitly ask
- avoid narrating every intermediate step when a shorter status is enough
- if progress updates are required, make them extremely minimal key points or emit the true packed context block instead of a human-readable paraphrase
- prefer execution first and defer explanation to the close-out
- keep early commentary limited to blockers, risky assumptions, and necessary progress updates
- store reusable handoffs and memory in `CCM1` or compact envelopes by default
- when context is compacted, use the packed output as the new active context instead of carrying the verbose version forward
- keep final summaries minimal too: key points, what changed, verification, and any remaining risk

Borrowed operating ideas from Caveman:

- brevity should be a persistent mode, not a one-off style toggle
- shorter outward explanations often improve speed and readability without hurting technical accuracy
- code, commands, file paths, exact errors, and other technical atoms stay normal and exact
- context savings should apply to both replies and stored memory, not just final prose
- completion summaries should stay concise and action-oriented instead of turning into changelogs

## How It Works

`compressoor` uses a deterministic compression protocol called `CCM1`.

At a high level:

1. Protect technical atoms that must survive exactly.
2. Normalize prose by removing filler and deduplicating repeated constraints.
3. Route the note into either generic `CCM1` sections or a compact template envelope.
4. Decode and score the result locally to detect loss.

Protected atoms include:

- file paths
- commands
- inline code
- quoted errors
- environment variables
- identifiers
- URLs

Compression happens through two paths:

- Generic `CCM1` blocks for broader notes.
- Compact envelopes such as `H1[...]`, `M1[...]`, `K1[...]`, `V1[...]`, and `E1[...]` for high-confidence patterns like handoffs, memory rules, bug-fix constraints, review findings, and explanation prompts.

For user-visible prose, `compressoor` also adopts a brevity policy:

- `lite`: compact but fully grammatical
- `std`: default, short direct prose with no filler
- `max`: telegraphic, intended for model-to-model handoff and stored context

For close-out summaries under `compressoor`:

- lead with what changed
- include only key verification
- mention only material remaining risk or blocker
- avoid file-by-file inventories unless explicitly requested
- prefer short bullets or a short paragraph over a long recap

Context replacement rule:

1. Pack verbose context into `CCM1` or a compact envelope.
2. Verify that critical atoms and constraints survived.
3. Treat the packed result as the active context going forward.
4. Drop the verbose working copy unless exact wording must be retained for legal, operational, or user-requested reasons.

The protocol reference lives in [`protocol.md`](/Users/max/compressoor/skills/compressoor/references/protocol.md).

## Scripts

Core scripts:

- [`pack_ccm.py`](/Users/max/compressoor/skills/compressoor/scripts/pack_ccm.py): deterministic packer
- [`unpack_ccm.py`](/Users/max/compressoor/skills/compressoor/scripts/unpack_ccm.py): structured decoder
- [`benchmark_ccm.py`](/Users/max/compressoor/skills/compressoor/scripts/benchmark_ccm.py): compression and token-style benchmark helper
- [`eval_roundtrip.py`](/Users/max/compressoor/skills/compressoor/scripts/eval_roundtrip.py): fidelity scorer
- [`run_corpus.py`](/Users/max/compressoor/skills/compressoor/scripts/run_corpus.py): batch corpus runner and stability gate

Example pack flow:

```bash
python3 skills/compressoor/scripts/pack_ccm.py \
  --level auto \
  --domain code \
  --source-id auth_fix \
  note.txt
```

Example decode flow:

```bash
python3 skills/compressoor/scripts/unpack_ccm.py packed.txt
```

## Quick Start

Example source note:

```text
Fix auth middleware token expiry bug. Do not change the API contract.
Keep the current error message exactly the same.
The likely bug is that token expiry uses < instead of <=.
Update tests around the boundary case and do not introduce a database migration.
```

Packed with `--level auto`:

```text
K1[api=stable;g=auth-fix;err=exact;mig=no;bt=todo;cmp=<,<=]
```

Decoded with `unpack_ccm.py`:

```text
Header: K1
Goals:
- fix the authentication middleware
Constraints:
- do not change the API contract
- keep the current error message exactly the same
- no DB migration
Decisions:
- the likely bug is that token expiry uses < instead of <=
Tests and verification:
- tests for the boundary case still need to be added
```

Typical local loop:

```bash
python3 skills/compressoor/scripts/pack_ccm.py --level auto --domain code --source-id auth_fix note.txt > packed.txt
python3 skills/compressoor/scripts/benchmark_ccm.py note.txt packed.txt
python3 skills/compressoor/scripts/eval_roundtrip.py note.txt packed.txt
python3 skills/compressoor/scripts/unpack_ccm.py packed.txt
```

## Benchmarks

There are two benchmark tracks in this repository.

### 1. Corpus Track

This is the main correctness track for Codex memory and handoff compression. It measures:

- saved percent
- round-trip pass rate
- semantic fact recall
- repack stability

Run it with:

```bash
python3 skills/compressoor/scripts/run_corpus.py --level auto --check-stability
```

Current local corpus baseline:

- `cases: 19`
- `pass_rate: 19/19`
- `avg_saved_percent: 58.0`
- `avg_keyword_recall: 0.921`
- `avg_semantic_fact_recall: 1.000`
- `stability_pass_rate: 19/19`

This is the main benchmark to trust for Codex-specific memory compression.

### 2. Caveman-Style Comparison Track

This is an adapted comparison suite inspired by Caveman’s README tasks. It is useful for directional comparison on terse explanation and instruction prompts, but it is not an apples-to-apples execution of Caveman’s own benchmark implementation.

Run it with:

```bash
python3 benchmarks/compare_to_caveman.py
```

Current local comparison baseline:

- `cases: 15`
- `compressoor_avg_saved_pct: 70.4`
- `caveman_readme_avg_saved_pct: 65.0`

Representative cases from the current suite:

- `react_rerender_bug: 58.7%`
- `auth_expiry_fix: 81.2%`
- `microservices_vs_monolith: 67.9%`
- `docker_multi_stage: 53.5%`
- `react_error_boundary: 70.6%`

Benchmark inputs live in [`caveman_style_cases.jsonl`](/Users/max/compressoor/benchmarks/caveman_style_cases.jsonl), and the README reference numbers used for directional comparison live in [`caveman_reference.json`](/Users/max/compressoor/benchmarks/caveman_reference.json).

## Tests

Run the regression suite with:

```bash
python3 -m unittest discover -s tests/compressoor -p 'test_*.py'
```

The test suite covers:

- corpus thresholds
- compact-envelope routing
- benchmark harness output
- plugin prompt defaults
- compacted context replaces verbose active context by default

## Notes

- The corpus and comparison results are local repository baselines, not universal guarantees.
- The standalone skill copy under [`skills/compressoor`](/Users/max/compressoor/skills/compressoor) is the main editable source.
- The plugin copy under [`plugins/compressoor`](/Users/max/compressoor/plugins/compressoor) should be kept in sync when compressor logic changes.

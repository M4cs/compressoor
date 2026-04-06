# compressoor

Aggressive low-loss context compression for Codex.

`Benchmarks` • `Example` • `Install` • `Usage` • `How It Works` • `Layout` • `Tests`

`compressoor` is a Codex plugin and standalone skill for compressing handoffs, repo memory, review findings, deploy notes, debug state, and generic working context into compact envelopes while preserving technical atoms and validating round-trip fidelity locally.

Inspired by the README structure in [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman), but built for Codex context and memory compression rather than response-style compression.

## Benchmarks

Local baselines are the point of this repo, so they lead the page.

### Corpus Baseline

This is the main benchmark to trust for Codex memory and handoff compression.

Run it with:

```bash
python3 skills/compressoor/scripts/run_corpus.py --level auto --check-stability
```

| Metric | Result |
|------|------:|
| Cases | 19 |
| Round-trip pass rate | 19/19 |
| Average saved | 58.0% |
| Average keyword recall | 0.921 |
| Average semantic fact recall | 1.000 |
| Stability pass rate | 19/19 |

By domain:

| Domain | Pass Rate | Avg Saved | Keyword Recall | Fact Recall | Stability |
|------|------:|------:|------:|------:|------:|
| `code` | 9/9 | 52.1% | 0.906 | 1.000 | 9/9 |
| `debug` | 2/2 | 62.7% | 0.903 | 1.000 | 2/2 |
| `frontend` | 2/2 | 62.0% | 0.979 | 1.000 | 2/2 |
| `ops` | 2/2 | 62.8% | 0.940 | 1.000 | 2/2 |
| `repo` | 2/2 | 69.8% | 0.886 | 1.000 | 2/2 |
| `review` | 2/2 | 59.6% | 0.964 | 1.000 | 2/2 |

### Caveman-Style Comparison

This is an adapted comparison suite inspired by Caveman's README tasks. It is directional, not an apples-to-apples execution of Caveman's own benchmark implementation.

Run it with:

```bash
python3 benchmarks/compare_to_caveman.py
```

| Track | Average Saved |
|------|------:|
| `compressoor` local suite | 70.4% |
| Caveman README reference | 65.0% |

Representative cases:

| Case | Saved | Fact Recall |
|------|------:|------:|
| `react_rerender_bug` | 58.7% | 1.000 |
| `auth_expiry_fix` | 81.2% | 0.867 |
| `postgres_pool_setup` | 76.7% | 1.000 |
| `git_rebase_merge` | 80.0% | 1.000 |
| `security_review` | 77.0% | 1.000 |
| `callback_async_await` | 84.1% | 1.000 |
| `microservices_vs_monolith` | 67.9% | 1.000 |
| `docker_multi_stage` | 53.5% | 1.000 |
| `postgres_race_condition` | 85.5% | 1.000 |
| `react_error_boundary` | 70.6% | 1.000 |

Benchmark inputs live in [`benchmarks/caveman_style_cases.jsonl`](benchmarks/caveman_style_cases.jsonl), and the README reference values used for directional comparison live in [`benchmarks/caveman_reference.json`](benchmarks/caveman_reference.json).

> [!IMPORTANT]
> These numbers are local repository baselines, not universal guarantees. The corpus track is the primary correctness benchmark.

## Example

### Source -> Packed -> Decoded

| Stage | Example |
|------|------|
| Source note | `Fix auth middleware token expiry bug. Keep the API contract and exact error message unchanged. Update the boundary-case tests. No database migration.` |
| Packed with `--level auto` | `K1[api=stable;g=auth-fix;err=exact;mig=no;bt=todo;cmp=<,<=]` |
| Decoded summary | `Goals: fix auth middleware`<br>`Constraints: API stable, exact error text, no DB migration`<br>`Tests: boundary case still needs coverage` |

### Typical Local Loop

| Command | Purpose |
|------|------|
| `python3 skills/compressoor/scripts/pack_ccm.py --level auto --domain code --source-id auth_fix note.txt > packed.txt` | Pack a verbose note into `CCM1` or a compact envelope |
| `python3 skills/compressoor/scripts/benchmark_ccm.py note.txt packed.txt` | Measure compression on the packed output |
| `python3 skills/compressoor/scripts/eval_roundtrip.py note.txt packed.txt` | Score fidelity and recall |
| `python3 skills/compressoor/scripts/unpack_ccm.py packed.txt` | Decode the packed output back into structured prose |

## Install

### Install As A Local Codex Plugin

1. Clone or copy this repository somewhere under your home directory.
2. Open Codex in the repository root.
3. Run `/plugins`.
4. Choose the local plugin at [`plugins/compressoor/.codex-plugin/plugin.json`](plugins/compressoor/.codex-plugin/plugin.json).
5. Install `Compressoor`.

The plugin bundles the skill under [`plugins/compressoor/skills/compressoor`](plugins/compressoor/skills/compressoor).

### Use As A Standalone Skill

If you want the skill without installing the plugin, use the standalone copy at [`skills/compressoor`](skills/compressoor).

Typical triggers:

- `$compressoor`
- `compress this handoff`
- `pack this memory file`
- `compress these repo rules`
- `benchmark this context block`

## Usage

`compressoor` is intended to be a default operating mode across projects, not just an on-demand tool.

What it compresses well:

- handoff notes
- repo rules and project memory
- bug-fix constraints
- review findings
- deploy and debug state
- concise explanation prompts

Installed-plugin defaults:

- compress working context even when the user did not explicitly ask
- avoid narrating every intermediate step when a shorter status is enough
- surface blockers and risky assumptions early, but defer extra explanation
- store reusable handoffs and memory in `CCM1` or compact envelopes by default
- replace verbose working context with the packed form once it validates
- keep final summaries short: outcome, verification, remaining risk

Borrowed operating ideas from Caveman:

- brevity should be a persistent mode, not a one-off toggle
- shorter outward explanations often improve speed and readability
- code, commands, file paths, errors, and other technical atoms stay exact
- context savings should apply to stored memory as well as visible replies

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

Compression paths:

- Generic `CCM1` blocks for broader notes
- Compact envelopes like `H1[...]`, `M1[...]`, `K1[...]`, `V1[...]`, and `E1[...]` for high-confidence patterns such as handoffs, memory rules, bug-fix constraints, review findings, and explanation prompts

Output brevity modes:

| Level | Use |
|------|------|
| `lite` | Compact but fully grammatical |
| `std` | Default, short direct prose with no filler |
| `max` | Telegraphic, intended for model-to-model handoff and stored context |

Context replacement rule:

1. Pack verbose context into `CCM1` or a compact envelope.
2. Verify that critical atoms and constraints survived.
3. Treat the packed result as the active context going forward.
4. Drop the verbose working copy unless exact wording must be retained.

The protocol reference lives in [`skills/compressoor/references/protocol.md`](skills/compressoor/references/protocol.md).

## Layout

```text
compressoor/
├── plugins/compressoor/           # Codex plugin package
├── skills/compressoor/            # Standalone skill copy
├── benchmarks/                    # Comparison fixtures and harnesses
└── tests/compressoor/             # Regression and benchmark tests
```

Core scripts:

| Script | Purpose |
|------|------|
| [`pack_ccm.py`](skills/compressoor/scripts/pack_ccm.py) | Deterministic packer |
| [`unpack_ccm.py`](skills/compressoor/scripts/unpack_ccm.py) | Structured decoder |
| [`benchmark_ccm.py`](skills/compressoor/scripts/benchmark_ccm.py) | Compression and token-style benchmark helper |
| [`eval_roundtrip.py`](skills/compressoor/scripts/eval_roundtrip.py) | Fidelity scorer |
| [`run_corpus.py`](skills/compressoor/scripts/run_corpus.py) | Batch corpus runner and stability gate |

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

- The standalone skill copy under [`skills/compressoor`](skills/compressoor) is the main editable source.
- The plugin copy under [`plugins/compressoor`](plugins/compressoor) should be kept in sync when compressor logic changes.

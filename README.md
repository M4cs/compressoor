# compressoor

Low-loss context compression for Codex.

| ✦ | What |
|---|---|
| 🧠 | Packs handoffs, repo memory, review notes, debug state, and constraints into `CCM1` or compact envelopes |
| 🎯 | Preserves technical atoms like commands, paths, identifiers, errors, and URLs |
| 🔁 | Validates round-trip fidelity locally instead of trusting vibes |
| 🧩 | Ships as both a Codex plugin and a standalone skill |

## Snapshot

| 📊 Corpus baseline | Value |
|---|---:|
| Cases | 19 |
| Round-trip pass | 19/19 |
| Avg saved | 58.0% |
| Avg keyword recall | 0.921 |
| Avg fact recall | 1.000 |
| Stability pass | 19/19 |

| 🗂️ Domain | Pass | Avg saved | Keyword | Facts | Stability |
|---|---:|---:|---:|---:|---:|
| `code` | 9/9 | 52.1% | 0.906 | 1.000 | 9/9 |
| `debug` | 2/2 | 62.7% | 0.903 | 1.000 | 2/2 |
| `frontend` | 2/2 | 62.0% | 0.979 | 1.000 | 2/2 |
| `ops` | 2/2 | 62.8% | 0.940 | 1.000 | 2/2 |
| `repo` | 2/2 | 69.8% | 0.886 | 1.000 | 2/2 |
| `review` | 2/2 | 59.6% | 0.964 | 1.000 | 2/2 |

Run the main corpus benchmark:

```bash
python3 skills/compressoor/scripts/run_corpus.py --level auto --check-stability
```

## Quick Example

| Stage | Output |
|---|---|
| Source | `Fix auth middleware token expiry bug. Keep the API contract and exact error message unchanged. Update the boundary-case tests. No database migration.` |
| Packed | `K1[api=stable;g=auth-fix;err=exact;mig=no;bt=todo;cmp=<,<=]` |
| Decoded | `Goals: fix auth middleware`<br>`Constraints: API stable, exact error text, no DB migration`<br>`Tests: boundary case still needs coverage` |

## Install

| 🚀 Path | Command / Target |
|---|---|
| Plugin | [`plugins/compressoor/.codex-plugin/plugin.json`](plugins/compressoor/.codex-plugin/plugin.json) |
| Standalone skill | [`skills/compressoor`](skills/compressoor) |
| Global hook installer | `python3 skills/compressoor/scripts/install_codex_compressoor.py --force` |
| Packed launcher | `python3 skills/compressoor/scripts/launch_codex_compressoor.py -- -C /path/to/repo` |

### Codex plugin

1. Open `/plugins`.
2. Select [`plugins/compressoor/.codex-plugin/plugin.json`](plugins/compressoor/.codex-plugin/plugin.json).
3. Install `Compressoor`.

### Global default mode

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force
```

That installer writes:

| File | Effect |
|---|---|
| `~/.codex/AGENTS.md` | makes compressoor the default behavior |
| `~/.codex/hooks.json` | injects packed hook enforcement |
| `~/.codex/config.toml` | enables `codex_hooks = true` |

Optional project-level `AGENTS.md` install:

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force \
  --project-agents /path/to/repo/AGENTS.md
```

### Packed bootstrap launcher

```bash
python3 skills/compressoor/scripts/launch_codex_compressoor.py --print-bootstrap
python3 skills/compressoor/scripts/launch_codex_compressoor.py -- -C /path/to/repo
python3 skills/compressoor/scripts/launch_codex_compressoor.py --prompt "Review this repo for regressions." -- -C /path/to/repo
```

## Use

| ✅ Good fits | Triggers |
|---|---|
| handoffs, repo rules, debug state, review findings, deploy notes, bug-fix constraints | `$compressoor`, `compress this handoff`, `pack this memory file`, `benchmark this context block` |

| ⚙️ Default behavior | Meaning |
|---|---|
| Compress by default | context gets packed even without an explicit user ask |
| Tool-first | avoid narration before useful actions |
| Packed updates only | if progress is required, emit encoder-produced `CCM1` or compact envelopes |
| Reusable memory stays packed | handoffs and stored context default to compressed form |
| Final replies stay short | outcome, verification, risk |

| 🧱 Enforcement layer | Path |
|---|---|
| Plugin prompt | plugin `defaultPrompt` |
| Workspace policy | [`AGENTS.md`](AGENTS.md) |
| Repo hooks | [`.codex/hooks.json`](.codex/hooks.json) |
| Global installer | [`skills/compressoor/scripts/install_codex_compressoor.py`](skills/compressoor/scripts/install_codex_compressoor.py) |
| Launcher | [`skills/compressoor/scripts/launch_codex_compressoor.py`](skills/compressoor/scripts/launch_codex_compressoor.py) |

## How it packs

| Step | What happens |
|---|---|
| 1 | Protect exact atoms: paths, commands, code, quoted errors, env vars, identifiers, URLs |
| 2 | Strip filler and merge repeated constraints |
| 3 | Route to generic `CCM1` or a compact template |
| 4 | Decode and score locally before trusting it |

| 🧪 Mode | Style |
|---|---|
| `lite` | compact, still fully grammatical |
| `std` | short and direct |
| `max` | telegraphic, best for model-to-model handoff |

Compact templates include `H1[...]`, `M1[...]`, `K1[...]`, `V1[...]`, and `E1[...]`.

Protocol reference: [`skills/compressoor/references/protocol.md`](skills/compressoor/references/protocol.md)

## Tooling

| Script | Purpose |
|---|---|
| [`pack_ccm.py`](skills/compressoor/scripts/pack_ccm.py) | deterministic packer |
| [`unpack_ccm.py`](skills/compressoor/scripts/unpack_ccm.py) | structured decoder |
| [`benchmark_ccm.py`](skills/compressoor/scripts/benchmark_ccm.py) | compression benchmark helper |
| [`eval_roundtrip.py`](skills/compressoor/scripts/eval_roundtrip.py) | fidelity scorer |
| [`run_corpus.py`](skills/compressoor/scripts/run_corpus.py) | batch corpus runner + stability gate |
| [`launch_codex_compressoor.py`](skills/compressoor/scripts/launch_codex_compressoor.py) | packed Codex launcher |
| [`session_start_hook.py`](skills/compressoor/scripts/session_start_hook.py) | session bootstrap hook |
| [`user_prompt_submit_hook.py`](skills/compressoor/scripts/user_prompt_submit_hook.py) | per-turn prompt hook |

## Repo shape

```text
compressoor/
├── plugins/compressoor/
├── skills/compressoor/
├── benchmarks/
└── tests/compressoor/
```

The editable source lives in [`skills/compressoor`](skills/compressoor). Keep [`plugins/compressoor`](plugins/compressoor) in sync when skill logic changes.

## Tests

```bash
python3 -m unittest discover -s tests/compressoor -p 'test_*.py'
```

Coverage includes corpus thresholds, template routing, benchmark output, plugin defaults, hook output, installer defaults, and packed-context replacement behavior.

## Notes

| 🔎 Caveman-style comparison | Value |
|---|---:|
| `compressoor` local suite | 70.4% saved |
| Caveman README reference | 65.0% saved |

Reference inputs:

- [`benchmarks/caveman_style_cases.jsonl`](benchmarks/caveman_style_cases.jsonl)
- [`benchmarks/caveman_reference.json`](benchmarks/caveman_reference.json)

> [!IMPORTANT]
> Benchmarks here are local repo baselines, not universal guarantees. The corpus track is the one to trust.

# compressoor

Compressoor is a concise runtime policy for Codex and Claude Code.

Its main job is to cut token overhead without making the agent sound unnatural. The style target is tool-first execution with no pre-tool chatter, no mid-loop chatter, no plan/thinking preambles before the first tool call, and short professional output after the loop. It also includes a small set of tools for compressing durable context such as handoffs, review notes, constraint summaries, and benchmark prompts.

## What it is

- A Codex skill and plugin plus a Claude Code plugin for concise runtime behavior
- A small set of scripts for prompt compaction, rendering short live context, and benchmarking token savings
- Session bootstrap hooks and an optional launcher for Codex

## Style target

- tool-first
- no pre-tool or mid-loop status text
- no initial plans or thinking summaries before the first tool call
- brief and professional
- no acknowledgements or filler
- no step-by-step narration unless it changes the plan
- short final answers with verification, blockers, and risks only when they matter

This is closer to "do the work first, then say less and keep it normal" than to character-role compression. The goal is lower token use without caveman speech.

## Install

### Fast Install From GitHub

If an agent or user only has the GitHub URL, this is the shortest Codex-friendly install path:

```bash
git clone https://github.com/M4cs/compressoor.git
cd compressoor
python3 skills/compressoor/scripts/install_codex_compressoor.py --force
```

If the repo is already cloned somewhere else, run the installer from that checkout.

Suggested prompt for an agent:

```text
Clone https://github.com/M4cs/compressoor if it is not already present, change into that checkout, then run python3 skills/compressoor/scripts/install_codex_compressoor.py --force. After that, confirm that ~/.codex/AGENTS.md, ~/.codex/hooks.json, ~/.agents/plugins/marketplace.json, and ~/plugins/compressoor exist.
```

### Codex Plugin

Install the plugin from [`plugins/compressoor/.codex-plugin/plugin.json`](plugins/compressoor/.codex-plugin/plugin.json).

### Claude Code Plugin

Add this repository as a Claude marketplace, then install `compressoor`:

```bash
claude plugin marketplace add M4cs/compressoor
claude plugin install compressoor@compressoor
```

The Claude plugin ships:

- [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)
- [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)
- [`.claude/agents/compressoor.md`](.claude/agents/compressoor.md)
- [`.claude/commands/compressoor.md`](.claude/commands/compressoor.md)

### Standalone runtime policy

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force
```

This writes:

- `~/.codex/AGENTS.md` with compressoor runtime guidance
- `~/.codex/hooks.json` with `SessionStart` and `SessionResume` runtime-policy hooks
- `~/.agents/plugins/marketplace.json` with a home-local `compressoor` marketplace entry
- `~/plugins/compressoor` as a symlink to this repo's plugin directory

The installed hooks inject a mandatory compressoor session directive automatically on session start and resume. That directive is meant to reduce token use by:

- preferring tools before any outward text
- forbidding initial plans, thinking summaries, and intent statements before the first tool call
- suppressing acknowledgements and routine narration before and during tool loops
- suppressing explanations of intent before tool calls
- keeping outward answers short and professional
- using compaction tools only when reusable context actually needs shortening

If you update compressoor rules, rerun the installer so `~/.codex/hooks.json` still points at the current hook scripts:

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force
```

This also makes `compressoor` discoverable outside this repo, because Codex can resolve it from the home-local marketplace at `~/.agents/plugins/marketplace.json`.

If you also want the same note in a project `AGENTS.md`:

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force \
  --project-agents /path/to/repo/AGENTS.md
```

If a target `AGENTS.md` already exists, the installer appends the compressoor directive instead of replacing the file.

## Launch Codex With Compressoor

Use the launcher if you want a Codex session bootstrapped with the compressoor runtime policy:

```bash
python3 skills/compressoor/scripts/launch_codex_compressoor.py -- -C /path/to/repo
```

Useful variants:

```bash
python3 skills/compressoor/scripts/launch_codex_compressoor.py --print-bootstrap
python3 skills/compressoor/scripts/launch_codex_compressoor.py --prompt "Review this repo for regressions." -- -C /path/to/repo
```

If compressoor guidance is already present in repo or global `AGENTS.md`, or active compressoor hooks are already installed, the launcher does not prepend another bootstrap prompt.

## Runtime Behavior

When compressoor is active, the intended behavior is:

- tools first
- no acknowledgements, commentary, or progress updates before or during tool loops
- no initial plans, thinking summaries, or intent statements before the first tool call
- concise status only after the loop, unless blocked
- short final answers after the tool loop
- explain failures, blockers, verification, or changed files when needed

This mode is aimed at keeping token overhead small in long tool-driven sessions while still sounding like a normal competent assistant after the tool loop ends.

## Context Tools

Compressoor also includes explicit-use context tools when you want to:

- pack a handoff
- compress a memory note
- shorten review findings
- compact a constraint summary
- benchmark verbose vs compact prompt text

In practice, the simplest workflow is:

1. Take verbose reusable context.
2. Compact it once.
3. Reuse the shorter version in later prompts instead of resending the original prose.

In Claude Code, the explicit entry point is `/compressoor ...`. In Codex, use the installed plugin or scripts directly when you want packing behavior.

## Benchmarks

Run the direct prompt-compaction benchmark:

```bash
python3 benchmarks/benchmark_explicit_packed_context.py
```

This compares verbose prompt scaffolds against compacted prompt scaffolds and reports token savings for the compaction helpers. It includes:

- `compact`: full compacted form
- `compact_min`: shorter follow-up-oriented form

To measure live Codex token usage for the same A/B prompts:

```bash
python3 benchmarks/benchmark_explicit_packed_context.py --limit 5 --live-codex
python3 benchmarks/benchmark_explicit_packed_context.py --limit 5 --live-codex --repeats 3 --order alternate
```

There is also a Codex CLI integration benchmark:

```bash
python3 benchmarks/benchmark_codex_cli.py --limit 5
```

Use that one as a runtime and integration check, not as the primary savings benchmark.

## Main Files

- [`skills/compressoor/SKILL.md`](skills/compressoor/SKILL.md): runtime policy and compaction behavior
- [`skills/compressoor/scripts/compact_prompt.py`](skills/compressoor/scripts/compact_prompt.py): direct prompt compactor
- [`skills/compressoor/scripts/render_live_context.py`](skills/compressoor/scripts/render_live_context.py): short live-context renderer
- [`skills/compressoor/scripts/install_codex_compressoor.py`](skills/compressoor/scripts/install_codex_compressoor.py): installer for runtime-policy notes
- [`skills/compressoor/scripts/launch_codex_compressoor.py`](skills/compressoor/scripts/launch_codex_compressoor.py): session launcher
- [`benchmarks/benchmark_explicit_packed_context.py`](benchmarks/benchmark_explicit_packed_context.py): main benchmark runner

## Tests

```bash
python3 -m unittest discover -s tests/compressoor -p 'test_*.py'
```

## Repo Layout

```text
compressoor/
├── plugins/compressoor/
├── skills/compressoor/
├── benchmarks/
└── tests/compressoor/
```

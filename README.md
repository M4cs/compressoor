# compressoor

Compressoor is an explicit-use context compactor for Codex and Claude Code.

It is meant for cases where you intentionally want to shrink durable context such as handoffs, review notes, constraint summaries, or benchmark prompts. The packaged Codex setup also boots a tool-first low-chatter session policy through session start/resume hooks.

## What it is

- A Codex skill and plugin plus a Claude Code plugin for explicit prompt compaction
- A small set of scripts for direct prompt compaction, rendering short live context, and benchmarking compact context
- Session bootstrap hooks and an optional launcher for Codex

## What it is not

- Not an always-on repo policy
- Not a hidden background hook system
- Not something to invoke on every prompt by default

The current project setup is intentionally simple:

- `AGENTS.md` states that compressoor is for explicit context-packing tasks only
- the plugin `defaultPrompt` and agent prompts enforce tool-first minimal output
- installed hooks bootstrap compressoor session mode on `SessionStart` and `SessionResume`
- the session policy suppresses commentary/progress during tool loops
- post-tool answers are intentionally tiny: shortest correct result, with explanation only for failures, blockers, or changed files when needed
- the launcher adds the compressoor session prompt only when no compressoor policy or active compressoor hooks are already present

## Install

### Codex Plugin

Install the plugin from [`plugins/compressoor/.codex-plugin/plugin.json`](/Users/max/compressoor/plugins/compressoor/.codex-plugin/plugin.json).

### Claude Code Plugin

Add this repository as a Claude marketplace, then install `compressoor`:

```bash
claude plugin marketplace add max/compressoor
claude plugin install compressoor@compressoor
```

The Claude plugin ships:

- [`.claude-plugin/marketplace.json`](/Users/max/compressoor/.claude-plugin/marketplace.json)
- [`.claude-plugin/plugin.json`](/Users/max/compressoor/.claude-plugin/plugin.json)
- [`.claude/agents/compressoor.md`](/Users/max/compressoor/.claude/agents/compressoor.md)
- [`.claude/commands/compressoor.md`](/Users/max/compressoor/.claude/commands/compressoor.md)

### Standalone skill / explicit-use notes

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force
```

This writes:

- `~/.codex/AGENTS.md` with explicit-use guidance
- `~/.codex/hooks.json` with `SessionStart` and `SessionResume` bootstrap hooks

The installed hooks inject compressoor session policy automatically on session start and resume. That policy is meant to reduce token use by:

- calling tools silently whenever tools can advance the task
- suppressing acknowledgements, commentary, and progress updates during tool loops
- keeping post-tool answers extremely small

If you also want the same note in a project `AGENTS.md`:

```bash
python3 skills/compressoor/scripts/install_codex_compressoor.py --force \
  --project-agents /path/to/repo/AGENTS.md
```

## Launch Codex With Compressoor

Use the launcher if you want a Codex session bootstrapped with the explicit compressoor policy:

```bash
python3 skills/compressoor/scripts/launch_codex_compressoor.py -- -C /path/to/repo
```

Useful variants:

```bash
python3 skills/compressoor/scripts/launch_codex_compressoor.py --print-bootstrap
python3 skills/compressoor/scripts/launch_codex_compressoor.py --prompt "Review this repo for regressions." -- -C /path/to/repo
```

If compressoor guidance is already present in repo or global `AGENTS.md`, or active compressoor hooks are already installed, the launcher does not prepend another bootstrap prompt.

## Session Behavior

When compressoor session mode is active, the intended behavior is:

- tools first
- no commentary, acknowledgements, or progress updates before or during tool loops
- shortest correct result after the tool loop
- explain only failures, blockers, or changed files when needed

This stricter mode is aimed at keeping token overhead small in long tool-driven sessions.

## Use Cases

Use compressoor when you explicitly want to:

- pack a handoff
- compress a memory note
- shorten review findings
- compact a constraint summary
- benchmark verbose vs compact prompt text

In practice, the simplest workflow is:

1. Take verbose reusable context.
2. Compact it once.
3. Reuse the shorter version in later prompts instead of resending the original prose.

In Claude Code, the explicit entry point is `/compressoor ...`. In Codex, use the installed plugin/skill explicitly.

## Benchmarks

Run the direct prompt-compaction benchmark:

```bash
python3 benchmarks/benchmark_explicit_packed_context.py
```

This compares verbose prompt scaffolds against compacted prompt scaffolds and reports token savings. It includes:

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

Use that one as a runtime/integration check, not as the primary savings benchmark.

## Main Files

- [`skills/compressoor/SKILL.md`](/Users/max/compressoor/skills/compressoor/SKILL.md): explicit-use skill behavior
- [`skills/compressoor/scripts/compact_prompt.py`](/Users/max/compressoor/skills/compressoor/scripts/compact_prompt.py): direct prompt compactor
- [`skills/compressoor/scripts/render_live_context.py`](/Users/max/compressoor/skills/compressoor/scripts/render_live_context.py): short live-context renderer
- [`skills/compressoor/scripts/install_codex_compressoor.py`](/Users/max/compressoor/skills/compressoor/scripts/install_codex_compressoor.py): installer for explicit-use notes
- [`skills/compressoor/scripts/launch_codex_compressoor.py`](/Users/max/compressoor/skills/compressoor/scripts/launch_codex_compressoor.py): session launcher
- [`benchmarks/benchmark_explicit_packed_context.py`](/Users/max/compressoor/benchmarks/benchmark_explicit_packed_context.py): main benchmark runner

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

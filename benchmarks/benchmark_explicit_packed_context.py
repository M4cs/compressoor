#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import tiktoken


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "benchmarks" / "caveman_style_cases.jsonl"
COMPACT = ROOT / "skills" / "compressoor" / "scripts" / "compact_prompt.py"
DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
CONFIG_WARNING = (
    "Live Codex benchmarking needs network access and a working Codex auth setup. "
    "If your local run fails before producing usage events, verify `codex exec` works first."
)
TOKEN_KEYS = {
    "input": "input_tokens",
    "input_tokens": "input_tokens",
    "output": "output_tokens",
    "output_tokens": "output_tokens",
    "total": "total_tokens",
    "total_tokens": "total_tokens",
    "cached_input": "cached_input_tokens",
    "cached_input_tokens": "cached_input_tokens",
    "reasoning": "reasoning_tokens",
    "reasoning_tokens": "reasoning_tokens",
}


@dataclass
class Scenario:
    case_id: str
    domain: str
    turns: list[str]


@dataclass
class Usage:
    total_tokens: int
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class RunResult:
    usage: Usage
    stdout: str
    stderr: str


VARIANT_VERBOSE = "verbose"
VARIANT_COMPACT = "compact"
VARIANT_COMPACT_MIN = "compact_min"
BENCH_VARIANTS = [VARIANT_COMPACT, VARIANT_COMPACT_MIN]


def load_compact_module():
    spec = importlib.util.spec_from_file_location("compressoor_compact_prompt", COMPACT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPACT_MODULE = load_compact_module()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark direct prompt compaction with exact tokenizer counts and optional live Codex usage."
    )
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--encoding", default="o200k_base")
    parser.add_argument("--live-codex", action="store_true")
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"))
    parser.add_argument("--model", default="")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--order",
        choices=["verbose-first", "packed-first", "alternate"],
        default="alternate",
        help="Execution order for live A/B runs. Default alternates by trial to reduce order bias.",
    )
    return parser.parse_args()


def load_scenarios(path: Path, limit: int) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        turns = [str(turn).strip() for turn in payload.get("turns", []) if str(turn).strip()]
        if len(turns) < 2:
            source = str(payload.get("source", "")).strip()
            if not source:
                continue
            turns = [
                source,
                "Continue from earlier context. Give the shortest final checklist that keeps exact technical constraints.",
            ]
        scenarios.append(Scenario(case_id=payload["id"], domain=payload.get("domain", "general"), turns=turns))
    return scenarios[:limit] if limit > 0 else scenarios


def token_count(text: str, encoding_name: str) -> tuple[int, str]:
    try:
        enc = get_encoding(encoding_name)
        return len(enc.encode(text)), encoding_name
    except Exception:
        approx = max(1, round(len(text.encode("utf-8")) / 4))
        return approx, f"approx_bytes_div_4:{encoding_name}"


@lru_cache(maxsize=None)
def get_encoding(encoding_name: str):
    return tiktoken.get_encoding(encoding_name)


@lru_cache(maxsize=None)
def compact_text(text: str) -> str:
    return COMPACT_MODULE.compact_prompt(text).strip()


def build_verbose_followup(prior_context: str, followup: str) -> str:
    return f"CTX:\n{prior_context}\nREQ:\n{followup}\n"


def build_packed_followup(prior_context: str, followup: str, domain: str, source_id: str) -> str:
    compact = compact_text(prior_context)
    return f"CTX:\n{compact}\nREQ:\n{followup}\n"


def build_live_safe_followup(prior_context: str, followup: str, domain: str, source_id: str) -> str:
    return build_packed_followup(prior_context, followup, domain, source_id)


def build_live_safe_min_followup(prior_context: str, followup: str, domain: str, source_id: str) -> str:
    compact = compact_text(prior_context)
    lines = [line.strip() for line in compact.split(";") if line.strip()]
    trimmed = "; ".join(lines[:3])
    return f"CTX:\n{trimmed}\nREQ:\n{followup}\n"


def add_benchmark_nonce(prompt: str, nonce: str) -> str:
    return f"{prompt}\nBenchmark nonce: {nonce}\n"


def prepare_clean_workspace(dest: Path) -> None:
    shutil.copytree(ROOT, dest, dirs_exist_ok=True)
    for rel in ("AGENTS.md", ".codex/hooks.json"):
        path = dest / rel
        if path.exists():
            path.unlink()


def prepare_codex_home(dest: Path, source_home: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    source = source_home / "auth.json"
    if source.exists():
        shutil.copy2(source, dest / "auth.json")


def build_codex_command(codex_bin: str, workspace: Path, prompt: str, model: str) -> list[str]:
    cmd = [
        codex_bin,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--cd",
        str(workspace),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def normalize_usage_dict(payload: dict[str, Any]) -> Usage | None:
    mapped: dict[str, int] = {}
    for key, value in payload.items():
        if key not in TOKEN_KEYS or not isinstance(value, int):
            continue
        mapped[TOKEN_KEYS[key]] = value
    total = mapped.get("total_tokens")
    if total is None and ("input_tokens" in mapped or "output_tokens" in mapped or "reasoning_tokens" in mapped):
        total = mapped.get("input_tokens", 0) + mapped.get("output_tokens", 0) + mapped.get("reasoning_tokens", 0)
    if total is None or total == 0:
        return None
    return Usage(
        total_tokens=total,
        input_tokens=mapped.get("input_tokens", 0),
        output_tokens=mapped.get("output_tokens", 0),
        cached_input_tokens=mapped.get("cached_input_tokens", 0),
        reasoning_tokens=mapped.get("reasoning_tokens", 0),
    )


def find_usage_candidates(payload: Any) -> list[Usage]:
    candidates: list[Usage] = []
    if isinstance(payload, dict):
        normalized = normalize_usage_dict(payload)
        if normalized is not None:
            candidates.append(normalized)
        for value in payload.values():
            candidates.extend(find_usage_candidates(value))
    elif isinstance(payload, list):
        for item in payload:
            candidates.extend(find_usage_candidates(item))
    return candidates


def extract_usage_from_jsonl(output: str) -> Usage | None:
    candidates: list[Usage] = []
    for line in output.splitlines():
        text = line.strip()
        if not text.startswith("{"):
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        candidates.extend(find_usage_candidates(payload))
    if not candidates:
        return None
    return max(candidates, key=lambda usage: usage.total_tokens)


def run_codex_prompt(
    codex_bin: str,
    codex_home: Path,
    workspace: Path,
    prompt: str,
    timeout: int,
    model: str,
) -> RunResult:
    proc = subprocess.run(
        build_codex_command(codex_bin, workspace, prompt, model),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "CODEX_HOME": str(codex_home)},
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"codex exec failed in {workspace} with exit code {proc.returncode}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
            f"{CONFIG_WARNING}"
        )
    usage = extract_usage_from_jsonl(proc.stdout)
    if usage is None:
        raise RuntimeError(
            f"could not find token-usage data in codex output for {workspace}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
            f"{CONFIG_WARNING}"
        )
    return RunResult(usage=usage, stdout=proc.stdout, stderr=proc.stderr)


def build_variant_prompt(variant: str, prior: str, followup: str, domain: str, source_id: str) -> str:
    if variant == VARIANT_VERBOSE:
        return build_verbose_followup(prior, followup)
    if variant == VARIANT_COMPACT:
        return build_packed_followup(prior, followup, domain, source_id)
    if variant == VARIANT_COMPACT_MIN:
        return build_live_safe_min_followup(prior, followup, domain, source_id)
    raise ValueError(f"unknown variant: {variant}")


def print_offline_summary(
    scenarios: list[Scenario],
    encoding_name: str,
    live_results: dict[str, dict[str, list[RunResult]]] | None = None,
) -> None:
    totals = {VARIANT_VERBOSE: 0, VARIANT_COMPACT: 0, VARIANT_COMPACT_MIN: 0}
    encoding_used = encoding_name
    per_case_saved: dict[str, list[tuple[str, float]]] = {variant: [] for variant in BENCH_VARIANTS}
    per_domain_saved: dict[str, dict[str, list[float]]] = {}

    for scenario in scenarios:
        prior = scenario.turns[0]
        followup = scenario.turns[-1]
        variant_tokens: dict[str, int] = {}
        line_parts = [f"{scenario.case_id}:"]
        for variant in [VARIANT_VERBOSE, *BENCH_VARIANTS]:
            prompt = build_variant_prompt(variant, prior, followup, scenario.domain, f"{scenario.case_id}_prior")
            count, encoding_used = token_count(prompt, encoding_name)
            variant_tokens[variant] = count
            totals[variant] += count
            line_parts.append(f"{variant}_tokens={count}")
        for variant in BENCH_VARIANTS:
            saved = variant_tokens[VARIANT_VERBOSE] - variant_tokens[variant]
            saved_pct = 0.0 if variant_tokens[VARIANT_VERBOSE] == 0 else (saved / variant_tokens[VARIANT_VERBOSE]) * 100
            per_case_saved[variant].append((scenario.case_id, saved_pct))
            per_domain_saved.setdefault(scenario.domain, {}).setdefault(variant, []).append(saved_pct)
            line_parts.append(f"{variant}_saved_tokens={saved}")
            line_parts.append(f"{variant}_saved_pct={saved_pct:.1f}")
        if live_results and scenario.case_id in live_results:
            verbose_runs = live_results[scenario.case_id][VARIANT_VERBOSE]
            verbose_input_med = int(statistics.median([r.usage.input_tokens for r in verbose_runs]))
            verbose_total_med = int(statistics.median([r.usage.total_tokens for r in verbose_runs]))
            verbose_cached_med = int(statistics.median([r.usage.cached_input_tokens for r in verbose_runs]))
            line_parts.append(f"live_input_verbose={verbose_input_med}")
            line_parts.append(f"live_cached_input_verbose={verbose_cached_med}")
            line_parts.append(f"live_total_verbose={verbose_total_med}")
            for variant in BENCH_VARIANTS:
                variant_runs = live_results[scenario.case_id][variant]
                variant_input_med = int(statistics.median([r.usage.input_tokens for r in variant_runs]))
                variant_total_med = int(statistics.median([r.usage.total_tokens for r in variant_runs]))
                variant_cached_med = int(statistics.median([r.usage.cached_input_tokens for r in variant_runs]))
                line_parts.append(f"live_input_{variant}={variant_input_med}")
                line_parts.append(f"live_cached_input_{variant}={variant_cached_med}")
                line_parts.append(f"live_total_{variant}={variant_total_med}")
                line_parts.append(f"live_input_saved_{variant}={verbose_input_med - variant_input_med}")
                line_parts.append(f"live_total_saved_{variant}={verbose_total_med - variant_total_med}")
        print(" ".join(line_parts))

    print(f"encoding_used: {encoding_used}")
    print(f"cases: {len(scenarios)}")
    print(f"avg_verbose_tokens: {0 if not scenarios else totals[VARIANT_VERBOSE] / len(scenarios):.1f}")
    for variant in BENCH_VARIANTS:
        saved = totals[VARIANT_VERBOSE] - totals[variant]
        saved_pct = 0.0 if totals[VARIANT_VERBOSE] == 0 else (saved / totals[VARIANT_VERBOSE]) * 100
        print(f"avg_{variant}_tokens: {0 if not scenarios else totals[variant] / len(scenarios):.1f}")
        print(f"avg_saved_tokens_{variant}: {0 if not scenarios else saved / len(scenarios):.1f}")
        print(f"avg_saved_percent_{variant}: {saved_pct:.1f}")
        ranked = sorted(per_case_saved[variant], key=lambda item: item[1])
        if ranked:
            worst = ", ".join(f"{case}={pct:.1f}%" for case, pct in ranked[:3])
            best = ", ".join(f"{case}={pct:.1f}%" for case, pct in ranked[-3:])
            print(f"worst_{variant}: {worst}")
            print(f"best_{variant}: {best}")
    for domain in sorted(per_domain_saved):
        for variant in BENCH_VARIANTS:
            values = per_domain_saved[domain].get(variant, [])
            if values:
                print(f"domain_{domain}_{variant}_avg_saved_pct: {statistics.mean(values):.1f}")


def run_live_pair(
    args: argparse.Namespace,
    verbose_workspace: Path,
    compact_workspace: Path,
    live_safe_workspace: Path,
    verbose_home: Path,
    compact_home: Path,
    live_safe_home: Path,
    verbose_prompt: str,
    compact_prompt: str,
    live_safe_prompt: str,
    packed_first: bool,
) -> dict[str, RunResult]:
    if packed_first:
        compact_result = run_codex_prompt(
            codex_bin=args.codex_bin,
            codex_home=compact_home,
            workspace=compact_workspace,
            prompt=compact_prompt,
            timeout=args.timeout,
            model=args.model,
        )
        live_safe_result = run_codex_prompt(
            codex_bin=args.codex_bin,
            codex_home=live_safe_home,
            workspace=live_safe_workspace,
            prompt=live_safe_prompt,
            timeout=args.timeout,
            model=args.model,
        )
        verbose_result = run_codex_prompt(
            codex_bin=args.codex_bin,
            codex_home=verbose_home,
            workspace=verbose_workspace,
            prompt=verbose_prompt,
            timeout=args.timeout,
            model=args.model,
        )
        return {VARIANT_VERBOSE: verbose_result, VARIANT_COMPACT: compact_result, VARIANT_COMPACT_MIN: live_safe_result}
    verbose_result = run_codex_prompt(
        codex_bin=args.codex_bin,
        codex_home=verbose_home,
        workspace=verbose_workspace,
        prompt=verbose_prompt,
        timeout=args.timeout,
        model=args.model,
    )
    compact_result = run_codex_prompt(
        codex_bin=args.codex_bin,
        codex_home=compact_home,
        workspace=compact_workspace,
        prompt=compact_prompt,
        timeout=args.timeout,
        model=args.model,
    )
    live_safe_result = run_codex_prompt(
        codex_bin=args.codex_bin,
        codex_home=live_safe_home,
        workspace=live_safe_workspace,
        prompt=live_safe_prompt,
        timeout=args.timeout,
        model=args.model,
    )
    return {VARIANT_VERBOSE: verbose_result, VARIANT_COMPACT: compact_result, VARIANT_COMPACT_MIN: live_safe_result}


def run_live_comparison(args: argparse.Namespace, scenarios: list[Scenario]) -> dict[str, dict[str, list[RunResult]]]:
    results: dict[str, dict[str, list[RunResult]]] = {}
    with tempfile.TemporaryDirectory(prefix="compressoor_explicit_ctx_") as td:
        tmp_root = Path(td)
        for scenario in scenarios:
            per_variant = {VARIANT_VERBOSE: [], VARIANT_COMPACT: [], VARIANT_COMPACT_MIN: []}
            for trial in range(args.repeats):
                verbose_workspace = tmp_root / f"{scenario.case_id}_verbose_workspace_{trial}"
                compact_workspace = tmp_root / f"{scenario.case_id}_compact_workspace_{trial}"
                live_safe_workspace = tmp_root / f"{scenario.case_id}_compact_min_workspace_{trial}"
                verbose_home = tmp_root / f"{scenario.case_id}_verbose_home_{trial}"
                compact_home = tmp_root / f"{scenario.case_id}_compact_home_{trial}"
                live_safe_home = tmp_root / f"{scenario.case_id}_compact_min_home_{trial}"
                prepare_clean_workspace(verbose_workspace)
                prepare_clean_workspace(compact_workspace)
                prepare_clean_workspace(live_safe_workspace)
                prepare_codex_home(verbose_home, args.codex_home)
                prepare_codex_home(compact_home, args.codex_home)
                prepare_codex_home(live_safe_home, args.codex_home)
                prior = scenario.turns[0]
                followup = scenario.turns[-1]
                nonce = f"{scenario.case_id}-trial-{trial}"
                verbose_prompt = add_benchmark_nonce(build_verbose_followup(prior, followup), nonce)
                compact_prompt = add_benchmark_nonce(
                    build_packed_followup(prior, followup, scenario.domain, f"{scenario.case_id}_prior"),
                    nonce,
                )
                live_safe_prompt = add_benchmark_nonce(
                    build_live_safe_followup(prior, followup, scenario.domain, f"{scenario.case_id}_prior"),
                    nonce,
                )
                if args.order == "packed-first":
                    packed_first = True
                elif args.order == "verbose-first":
                    packed_first = False
                else:
                    packed_first = trial % 2 == 1
                trial_results = run_live_pair(
                    args,
                    verbose_workspace,
                    compact_workspace,
                    live_safe_workspace,
                    verbose_home,
                    compact_home,
                    live_safe_home,
                    verbose_prompt,
                    compact_prompt,
                    live_safe_prompt,
                    packed_first=packed_first,
                )
                for variant, result in trial_results.items():
                    per_variant[variant].append(result)
            results[scenario.case_id] = per_variant
    return results


def main() -> int:
    args = parse_args()
    scenarios = load_scenarios(args.scenarios, args.limit)
    live_results: dict[str, dict[str, list[RunResult]]] | None = None
    if args.live_codex:
        live_results = run_live_comparison(args, scenarios)
    print_offline_summary(scenarios, args.encoding, live_results)
    if live_results:
        verbose_input = sum(int(statistics.median([r.usage.input_tokens for r in per_variant[VARIANT_VERBOSE]])) for per_variant in live_results.values())
        verbose_total = sum(int(statistics.median([r.usage.total_tokens for r in per_variant[VARIANT_VERBOSE]])) for per_variant in live_results.values())
        print("live_summary:")
        print(f"live_verbose_input_tokens: {verbose_input}")
        print(f"live_verbose_total_tokens: {verbose_total}")
        for variant in BENCH_VARIANTS:
            variant_input = sum(int(statistics.median([r.usage.input_tokens for r in per_variant[variant]])) for per_variant in live_results.values())
            variant_total = sum(int(statistics.median([r.usage.total_tokens for r in per_variant[variant]])) for per_variant in live_results.values())
            input_saved = verbose_input - variant_input
            total_saved = verbose_total - variant_total
            input_saved_pct = 0.0 if verbose_input == 0 else (input_saved / verbose_input) * 100
            total_saved_pct = 0.0 if verbose_total == 0 else (total_saved / verbose_total) * 100
            print(f"live_{variant}_input_tokens: {variant_input}")
            print(f"live_input_saved_tokens_{variant}: {input_saved}")
            print(f"live_input_saved_percent_{variant}: {input_saved_pct:.1f}")
            print(f"live_{variant}_total_tokens: {variant_total}")
            print(f"live_total_saved_tokens_{variant}: {total_saved}")
            print(f"live_total_saved_percent_{variant}: {total_saved_pct:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

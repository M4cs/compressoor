#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "compressoor"
PACK = SKILL_ROOT / "scripts" / "pack_ccm.py"
EVAL = SKILL_ROOT / "scripts" / "eval_roundtrip.py"
BENCH = SKILL_ROOT / "scripts" / "benchmark_ccm.py"
CASES = ROOT / "benchmarks" / "caveman_style_cases.jsonl"
REF = ROOT / "benchmarks" / "caveman_reference.json"


def parse_metric(output: str, name: str) -> float:
    match = re.search(rf"^\s*{re.escape(name)}:\s+([0-9.]+)", output, re.M)
    if not match:
        raise RuntimeError(f"missing metric {name}")
    return float(match.group(1))


def fallback_saved_percent(source_text: str, packed_text: str) -> float:
    src = max(1, round(len(source_text.encode("utf-8")) / 4))
    packed = max(1, round(len(packed_text.encode("utf-8")) / 4))
    return ((src - packed) / src) * 100


def main() -> int:
    refs = json.loads(REF.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    ref_map = {entry["task"]: entry["caveman_saved_pct"] for entry in refs["benchmarks"]}
    total = 0.0
    for case in cases:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / f"{case['id']}.txt"
            packed = Path(td) / f"{case['id']}.packed"
            src.write_text(case["source"] + "\n", encoding="utf-8")
            packed_text = subprocess.run(
                ["python3", str(PACK), "--level", "auto", "--domain", case["domain"], "--source-id", case["id"], str(src)],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            packed.write_text(packed_text, encoding="utf-8")
            bench_proc = subprocess.run(["python3", str(BENCH), str(src), str(packed)], capture_output=True, text=True)
            bench = bench_proc.stdout
            eval_out = subprocess.run(["python3", str(EVAL), str(src), str(packed)], capture_output=True, text=True, check=True).stdout
            try:
                saved = parse_metric(bench, "saved_percent")
            except RuntimeError:
                saved = fallback_saved_percent(case["source"] + "\n", packed_text)
            facts = parse_metric(eval_out, "semantic_fact_recall")
            total += saved
            print(f"{case['id']}: compressoor_saved_pct={saved:.1f} semantic_fact_recall={facts:.3f}")
    print(f"compressoor_avg_saved_pct={total / len(cases):.1f}")
    print(f"caveman_readme_avg_saved_pct=65.0")
    print("caveman_reference_tasks:")
    for task, pct in ref_map.items():
        print(f"  - {task}: {pct}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

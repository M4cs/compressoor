#!/usr/bin/env python3
"""
Run CCM packing/evaluation over a JSONL corpus and summarize results.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "scripts" / "pack_ccm.py"
EVAL = ROOT / "scripts" / "eval_roundtrip.py"
BENCH = ROOT / "scripts" / "benchmark_ccm.py"
UNPACK = ROOT / "scripts" / "unpack_ccm.py"
DEFAULT_CORPUS = ROOT / "references" / "corpus.jsonl"


def parse_metric(output: str, name: str) -> float | None:
    match = re.search(rf"^{re.escape(name)}:\s+([0-9.]+)", output, re.M)
    return float(match.group(1)) if match else None


def parse_text_metric(output: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}:\s+(.+)$", output, re.M)
    return match.group(1).strip() if match else None


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def load_corpus(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CCM evaluation across a corpus.")
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--level", default="auto", choices=["auto", "lite", "std", "max"])
    parser.add_argument("--limit", type=int, default=0, help="Optional max number of corpus rows to run.")
    parser.add_argument("--check-stability", action="store_true", help="Also run pack->unpack->pack drift checks.")
    args = parser.parse_args()

    corpus = load_corpus(Path(args.corpus))
    if args.limit > 0:
        corpus = corpus[: args.limit]

    total = 0
    passed = 0
    total_saved_pct = 0.0
    total_keyword = 0.0
    total_fact = 0.0
    failures: list[str] = []
    stability_checked = 0
    stability_ok = 0
    by_domain: dict[str, dict[str, float]] = collections.defaultdict(
        lambda: {"cases": 0, "passed": 0, "saved": 0.0, "keyword": 0.0, "facts": 0.0, "stable": 0, "stable_checked": 0}
    )

    for row in corpus:
        total += 1
        source_text = row["source"].rstrip() + "\n"
        with tempfile.TemporaryDirectory() as td:
            source_path = Path(td) / f"{row['id']}.txt"
            packed_path = Path(td) / f"{row['id']}.packed"
            source_path.write_text(source_text, encoding="utf-8")

            pack_proc = subprocess.run(
                [
                    "python3",
                    str(PACK),
                    "--level",
                    args.level,
                    "--domain",
                    row.get("domain", "general"),
                    "--source-id",
                    row["id"],
                    str(source_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            packed_path.write_text(pack_proc.stdout, encoding="utf-8")

            eval_out = run(["python3", str(EVAL), str(source_path), str(packed_path)]).stdout
            bench_out = run(["python3", str(BENCH), str(source_path), str(packed_path)]).stdout

            keyword = parse_metric(eval_out, "keyword_recall") or 0.0
            fact = parse_metric(eval_out, "semantic_fact_recall") or 0.0
            saved_pct = parse_metric(bench_out, "saved_percent") or 0.0
            ok = parse_text_metric(eval_out, "roundtrip_ok") == "yes"

            total_keyword += keyword
            total_fact += fact
            total_saved_pct += saved_pct
            if ok:
                passed += 1
            else:
                failures.append(row["id"])

            domain = row.get("domain", "general")
            bucket = by_domain[domain]
            bucket["cases"] += 1
            bucket["saved"] += saved_pct
            bucket["keyword"] += keyword
            bucket["facts"] += fact
            if ok:
                bucket["passed"] += 1

            stable_text = ""
            stable_ok = None
            if args.check_stability:
                unpacked_path = Path(td) / f"{row['id']}.unpacked.txt"
                repacked_path = Path(td) / f"{row['id']}.repacked.txt"
                unpack_out = run(["python3", str(UNPACK), str(packed_path)]).stdout
                unpacked_path.write_text(unpack_out, encoding="utf-8")
                repack_out = run(
                    [
                        "python3",
                        str(PACK),
                        "--level",
                        args.level,
                        "--domain",
                        row.get("domain", "general"),
                        "--source-id",
                        row["id"],
                        str(unpacked_path),
                    ]
                ).stdout
                repacked_path.write_text(repack_out, encoding="utf-8")
                first_len = len(pack_proc.stdout.encode("utf-8"))
                second_len = len(repack_out.encode("utf-8"))
                drift_ratio = 0.0 if first_len == 0 else abs(second_len - first_len) / first_len
                stable_ok = drift_ratio <= 0.10
                stability_checked += 1
                bucket["stable_checked"] += 1
                if stable_ok:
                    stability_ok += 1
                    bucket["stable"] += 1
                stable_text = f" stable={'yes' if stable_ok else 'no'} drift={drift_ratio:.2f}"

            print(
                f"{row['id']}: roundtrip={'yes' if ok else 'review'} "
                f"saved_pct={saved_pct:.1f} keyword={keyword:.3f} facts={fact:.3f}{stable_text}"
            )

    avg_saved = 0.0 if total == 0 else total_saved_pct / total
    avg_keyword = 0.0 if total == 0 else total_keyword / total
    avg_fact = 0.0 if total == 0 else total_fact / total

    print(f"cases: {total}")
    print(f"pass_rate: {passed}/{total}")
    print(f"avg_saved_percent: {avg_saved:.1f}")
    print(f"avg_keyword_recall: {avg_keyword:.3f}")
    print(f"avg_semantic_fact_recall: {avg_fact:.3f}")
    if args.check_stability:
        print(f"stability_pass_rate: {stability_ok}/{stability_checked}")
    print("by_domain:")
    for domain in sorted(by_domain):
        bucket = by_domain[domain]
        cases = int(bucket["cases"])
        avg_dom_saved = 0.0 if cases == 0 else bucket["saved"] / cases
        avg_dom_keyword = 0.0 if cases == 0 else bucket["keyword"] / cases
        avg_dom_fact = 0.0 if cases == 0 else bucket["facts"] / cases
        suffix = ""
        if args.check_stability:
            suffix = f" stable={int(bucket['stable'])}/{int(bucket['stable_checked'])}"
        print(
            f"  {domain}: pass_rate={int(bucket['passed'])}/{cases} "
            f"avg_saved={avg_dom_saved:.1f} keyword={avg_dom_keyword:.3f} facts={avg_dom_fact:.3f}{suffix}"
        )
    if failures:
        print("failures:")
        for case_id in failures:
            print(f"  - {case_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

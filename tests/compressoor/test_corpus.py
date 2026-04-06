from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN_CORPUS = ROOT / "skills" / "compressoor" / "scripts" / "run_corpus.py"


def parse_metric(output: str, name: str) -> float:
    match = re.search(rf"^{re.escape(name)}:\s+([0-9.]+)", output, re.M)
    if not match:
        raise AssertionError(f"missing metric {name}\n{output}")
    return float(match.group(1))


class CorpusTests(unittest.TestCase):
    def test_corpus_thresholds(self) -> None:
        proc = subprocess.run(
            ["python3", str(RUN_CORPUS), "--level", "auto", "--check-stability"],
            capture_output=True,
            text=True,
            check=True,
        )
        out = proc.stdout
        self.assertIn("pass_rate: 19/19", out)
        self.assertIn("stability_pass_rate: 19/19", out)
        self.assertGreaterEqual(parse_metric(out, "avg_saved_percent"), 50.0)
        self.assertGreaterEqual(parse_metric(out, "avg_keyword_recall"), 0.90)
        self.assertGreaterEqual(parse_metric(out, "avg_semantic_fact_recall"), 1.0)

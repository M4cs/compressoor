from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPARE = ROOT / "benchmarks" / "compare_to_caveman.py"


class CavemanComparisonTests(unittest.TestCase):
    def test_comparison_harness_runs(self) -> None:
        proc = subprocess.run(["python3", str(COMPARE)], capture_output=True, text=True, check=True)
        out = proc.stdout
        self.assertIn("caveman_readme_avg_saved_pct=65.0", out)
        case_lines = re.findall(r"^[a-z0-9_]+:\s+compressoor_saved_pct=", out, re.M)
        self.assertGreaterEqual(len(case_lines), 15, out)
        match = re.search(r"compressoor_avg_saved_pct=([0-9.]+)", out)
        self.assertIsNotNone(match, out)
        self.assertGreaterEqual(float(match.group(1)), 65.0)

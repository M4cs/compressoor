from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "skills" / "compressoor" / "scripts" / "pack_ccm.py"


CASES = {
    "handoff": ("Current status: parser change is implemented in src/parser.ts, but integration tests are not run yet. Unit tests pass. The main unresolved issue is whether the new delimiter handling breaks legacy CSV imports. Next steps are to run integration tests and verify one old fixture before merging.", "H1["),
    "memory": ("This repository uses Bun for scripts, not npm. Prefer ripgrep for search. Avoid destructive git commands unless explicitly requested. If editing frontend code, preserve the existing design system and do not introduce a new font stack.", "M1["),
    "constraint": ("Auth fix is in src/auth.ts. Keep API stable. Keep the exact error text. Tests for the boundary case still need to be added. No DB migration.", "K1["),
    "review": ("Findings: src/cache.ts may leak stale entries after partial invalidation. Keep the external API unchanged. Add a regression test for concurrent invalidation. Risk: metrics dashboards currently rely on the old miss counter shape.", "V1["),
    "progress": ("Status: benchmarking in progress. Next step: verify token deltas.", "P1["),
}


class EnvelopeTests(unittest.TestCase):
    def test_compact_envelopes_selected(self) -> None:
        for name, (text, prefix) in CASES.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as td:
                    src = Path(td) / "src.txt"
                    src.write_text(text + "\n", encoding="utf-8")
                    proc = subprocess.run(
                        ["python3", str(PACK), "--level", "auto", "--domain", "code", "--source-id", name, str(src)],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertTrue(proc.stdout.startswith(prefix), proc.stdout)

    def test_instruction_like_text_does_not_use_compact_template(self) -> None:
        text = (
            "Use $compressoor by default across projects. Prefer compact envelopes for durable state. "
            "Tool calls first; no human-readable pre-tool status text. Use H1 M1 K1 V1 E1 when shorter."
        )
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            src.write_text(text + "\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(PACK), "--level", "auto", "--domain", "repo", "--source-id", "policy", str(src)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(proc.stdout.startswith("CCM1|"), proc.stdout)

    def test_skill_defaults_require_terse_execution_mode(self) -> None:
        skill = (ROOT / "skills" / "compressoor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("do not narrate every step", skill)
        self.assertIn("do not send routine plaintext progress updates", skill)
        self.assertIn("default to terse execution mode for every agent and sub-agent", skill)
        self.assertIn("do not send any human-readable pre-tool status message", skill)
        self.assertIn("never send any message before the current tool loop is complete", skill)
        self.assertIn("finish the loop first and explain only after the loop completes", skill)
        self.assertIn("store it in `CCM1` or a compact envelope", skill)
        self.assertIn("discard the verbose source and retain the packed state", skill)
        self.assertIn("Never expand summaries into human-readable play-by-play.", skill)
        self.assertIn("Never send a progress update.", skill)
        self.assertIn("Never send a human-readable pre-tool status message", skill)
        self.assertIn("Never interrupt an active tool-gathering or tool-execution loop with plaintext status.", skill)
        self.assertIn("Never hand-write a fake packed status for live progress.", skill)
        self.assertIn("Never bypass compressoor for reusable memory or handoffs.", skill)
        self.assertIn("Keep final close-out simplified but detailed.", skill)
        self.assertIn("keep final work summaries simplified but detailed: what was done, why it was done, key verification, material remaining risk only", skill)
        self.assertIn("Never send plaintext progress updates", skill)

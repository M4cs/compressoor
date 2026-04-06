#!/usr/bin/env python3
"""
Codex UserPromptSubmit hook that reinforces packed compressoor policy.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "skills" / "compressoor" / "scripts" / "pack_ccm.py"
POLICY = ROOT / "skills" / "compressoor" / "policy" / "turn_policy.txt"


def pack_text(text: str, source_id: str) -> str:
    proc = subprocess.run(
        ["python3", str(PACK), "--level", "std", "--domain", "repo", "--source-id", source_id],
        input=text,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def main() -> int:
    json.load(sys.stdin)
    packed = pack_text(POLICY.read_text(encoding="utf-8"), "turn_hook")
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": packed,
        }
    }
    json.dump(payload, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

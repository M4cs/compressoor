#!/usr/bin/env python3
"""
Launch interactive Codex with a packed compressoor bootstrap prompt.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "skills" / "compressoor" / "scripts" / "pack_ccm.py"
SESSION_POLICY = ROOT / "skills" / "compressoor" / "policy" / "session_policy.txt"
INTERACTIVE_SUBCOMMANDS = {
    "exec",
    "review",
    "login",
    "logout",
    "mcp",
    "mcp-server",
    "app-server",
    "app",
    "completion",
    "sandbox",
    "debug",
    "apply",
    "resume",
    "fork",
    "cloud",
    "features",
    "help",
}
SESSION_POLICY_TEXT = SESSION_POLICY.read_text(encoding="utf-8").strip()
# Policy text includes: Do not send any human-readable status message before a tool call.


def build_bootstrap() -> str:
    proc = subprocess.run(
        ["python3", str(PACK), "--level", "std", "--domain", "repo", "--source-id", "sess_boot"],
        input=SESSION_POLICY_TEXT,
        capture_output=True,
        text=True,
        check=True,
    )
    packed = proc.stdout.strip()
    if not packed or not (packed.startswith("CCM1|") or packed[:2] in {"H1", "M1", "K1", "V1", "E1"}):
        raise RuntimeError(f"unexpected bootstrap payload: {packed!r}")
    return packed


def compose_prompt(user_prompt: str | None) -> str:
    packed = build_bootstrap()
    if user_prompt:
        return f"{packed}\n{user_prompt}"
    return packed


def normalize_forward_args(argv: list[str]) -> list[str]:
    if argv and argv[0] == "--":
        return argv[1:]
    return argv


def reject_noninteractive_subcommands(argv: list[str]) -> None:
    for token in argv:
        if token == "--":
            continue
        if token.startswith("-"):
            continue
        if token in INTERACTIVE_SUBCOMMANDS:
            raise SystemExit(
                f"launch_codex_compressoor.py only wraps interactive `codex` sessions; got subcommand `{token}`"
            )
        break


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Codex with a packed compressoor session bootstrap.")
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"))
    parser.add_argument("--prompt", help="Optional user prompt appended after the packed bootstrap.")
    parser.add_argument(
        "--print-bootstrap",
        action="store_true",
        help="Print the packed startup payload and exit.",
    )
    parser.add_argument("codex_args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.print_bootstrap:
        print(build_bootstrap())
        return 0

    codex_args = normalize_forward_args(args.codex_args)
    reject_noninteractive_subcommands(codex_args)
    cmd = [args.codex_bin, *codex_args, compose_prompt(args.prompt)]
    os.execvp(args.codex_bin, cmd)


if __name__ == "__main__":
    raise SystemExit(main())

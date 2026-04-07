#!/usr/bin/env python3
"""Install compressoor's concise runtime policy into AGENTS and hooks files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GLOBAL_TEMPLATE = ROOT / "skills" / "compressoor" / "policy" / "global_agents.md"


def render_global_agents() -> str:
    return GLOBAL_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"


def hook_command(script_name: str) -> str:
    return f"python3 {ROOT / 'skills' / 'compressoor' / 'scripts' / script_name}"


def render_hooks_config() -> str:
    payload = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {"type": "command", "command": hook_command("session_start_hook.py")},
                    ]
                }
            ],
            "SessionResume": [
                {
                    "hooks": [
                        {"type": "command", "command": hook_command("session_resume_hook.py")},
                    ]
                }
            ],
        }
    }
    return json.dumps(payload, indent=2) + "\n"


def write_text(path: Path, content: str, force: bool = False) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return False
        if not force:
            raise FileExistsError(f"{path} already exists; rerun with --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install compressoor's concise runtime policy notes.")
    parser.add_argument("--global-agents", type=Path, default=Path.home() / ".codex" / "AGENTS.md")
    parser.add_argument("--global-hooks", type=Path, default=Path.home() / ".codex" / "hooks.json")
    parser.add_argument("--project-agents", type=Path, action="append", default=[])
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content = render_global_agents()
    hooks = render_hooks_config()

    for path in [args.global_agents, *args.project_agents]:
        changed = write_text(path, content, force=args.force)
        print(f"{'wrote' if changed else 'unchanged'} {path}")

    changed = write_text(args.global_hooks, hooks, force=args.force)
    print(f"{'wrote' if changed else 'unchanged'} {args.global_hooks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

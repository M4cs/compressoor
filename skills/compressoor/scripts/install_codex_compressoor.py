#!/usr/bin/env python3
"""
Install compressoor's default Codex policy into AGENTS, hooks, and config files.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GLOBAL_TEMPLATE = ROOT / "skills" / "compressoor" / "policy" / "global_agents.md"
SESSION_HOOK = ROOT / "skills" / "compressoor" / "scripts" / "session_start_hook.py"
TURN_HOOK = ROOT / "skills" / "compressoor" / "scripts" / "user_prompt_submit_hook.py"


def render_global_agents() -> str:
    return GLOBAL_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"


def render_hooks_config() -> str:
    payload = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'/usr/bin/python3 "{SESSION_HOOK}"',
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'/usr/bin/python3 "{TURN_HOOK}"',
                        }
                    ],
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


def enable_hooks_feature(config_path: Path) -> bool:
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
    else:
        text = ""

    if re.search(r"(?m)^codex_hooks\s*=\s*true\s*$", text):
        return False

    if "[features]" in text:
        updated = re.sub(r"(?ms)^\[features\]\n", "[features]\ncodex_hooks = true\n", text, count=1)
    else:
        prefix = "[features]\ncodex_hooks = true\n"
        updated = prefix if not text.strip() else prefix + "\n" + text.lstrip("\n")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install compressoor as the default Codex policy.")
    parser.add_argument("--global-agents", type=Path, default=Path.home() / ".codex" / "AGENTS.md")
    parser.add_argument("--global-hooks", type=Path, default=Path.home() / ".codex" / "hooks.json")
    parser.add_argument("--config", type=Path, default=Path.home() / ".codex" / "config.toml")
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

    changed = enable_hooks_feature(args.config)
    print(f"{'updated' if changed else 'unchanged'} {args.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

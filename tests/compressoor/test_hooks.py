from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOKS_JSON = ROOT / ".codex" / "hooks.json"
SESSION_HOOK = ROOT / "skills" / "compressoor" / "scripts" / "session_start_hook.py"
TURN_HOOK = ROOT / "skills" / "compressoor" / "scripts" / "user_prompt_submit_hook.py"
INSTALLER = ROOT / "skills" / "compressoor" / "scripts" / "install_codex_compressoor.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HookTests(unittest.TestCase):
    def test_repo_hooks_config_uses_supported_events(self) -> None:
        payload = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        hooks = payload["hooks"]
        self.assertIn("SessionStart", hooks)
        self.assertIn("UserPromptSubmit", hooks)
        session_cmd = hooks["SessionStart"][0]["hooks"][0]["command"]
        turn_cmd = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn("session_start_hook.py", session_cmd)
        self.assertIn("user_prompt_submit_hook.py", turn_cmd)
        self.assertIn("git rev-parse --show-toplevel", session_cmd)

    def test_session_start_hook_returns_packed_additional_context(self) -> None:
        proc = subprocess.run(
            ["python3", str(SESSION_HOOK)],
            input="{}",
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        out = payload["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SessionStart")
        ctx = out["additionalContext"]
        self.assertTrue(ctx.startswith("CCM1|") or ctx[:2] in {"H1", "M1", "K1", "V1", "E1"}, ctx)

    def test_user_prompt_submit_hook_returns_packed_additional_context(self) -> None:
        proc = subprocess.run(
            ["python3", str(TURN_HOOK)],
            input='{"prompt":"check repo"}',
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        out = payload["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "UserPromptSubmit")
        ctx = out["additionalContext"]
        self.assertTrue(ctx.startswith("CCM1|") or ctx[:2] in {"H1", "M1", "K1", "V1", "E1"}, ctx)

    def test_installer_renders_global_hooks_and_enables_feature(self) -> None:
        module = load_module(INSTALLER, "compressoor_installer")
        hooks = json.loads(module.render_hooks_config())
        self.assertIn("SessionStart", hooks["hooks"])
        self.assertIn("UserPromptSubmit", hooks["hooks"])

        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / "config.toml"
            config.write_text("[features]\napps = false\n", encoding="utf-8")
            changed = module.enable_hooks_feature(config)
            self.assertTrue(changed)
            text = config.read_text(encoding="utf-8")
            self.assertIn("codex_hooks = true", text)
            self.assertFalse(module.enable_hooks_feature(config))

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "skills" / "compressoor" / "scripts" / "launch_codex_compressoor.py"
PLUGIN_LAUNCHER = ROOT / "plugins" / "compressoor" / "skills" / "compressoor" / "scripts" / "launch_codex_compressoor.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionLauncherTests(unittest.TestCase):
    def test_launchers_exist_in_skill_and_plugin(self) -> None:
        self.assertTrue(LAUNCHER.exists())
        self.assertTrue(PLUGIN_LAUNCHER.exists())

    def test_bootstrap_is_packed(self) -> None:
        module = load_module(LAUNCHER, "compressoor_launcher")
        packed = module.build_bootstrap()
        self.assertTrue(packed.startswith("CCM1|") or packed[:2] in {"H1", "M1", "K1", "V1", "E1"}, packed)
        self.assertNotIn("human-readable status message", packed)

    def test_compose_prompt_keeps_packed_bootstrap_first(self) -> None:
        module = load_module(LAUNCHER, "compressoor_launcher_prompt")
        prompt = module.compose_prompt("Fix the failing test.")
        self.assertTrue(prompt.startswith("CCM1|") or prompt[:2] in {"H1", "M1", "K1", "V1", "E1"}, prompt)
        self.assertTrue(prompt.endswith("\nFix the failing test."), prompt)

    def test_noninteractive_subcommands_are_rejected(self) -> None:
        module = load_module(LAUNCHER, "compressoor_launcher_reject")
        with self.assertRaises(SystemExit):
            module.reject_noninteractive_subcommands(["exec", "fix bug"])

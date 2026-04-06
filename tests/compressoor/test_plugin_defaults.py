from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = ROOT / "plugins" / "compressoor" / ".codex-plugin" / "plugin.json"
AGENT_YAML_PATHS = [
    ROOT / "skills" / "compressoor" / "agents" / "openai.yaml",
    ROOT / "plugins" / "compressoor" / "skills" / "compressoor" / "agents" / "openai.yaml",
]
LAUNCHER_PATHS = [
    ROOT / "skills" / "compressoor" / "scripts" / "launch_codex_compressoor.py",
    ROOT / "plugins" / "compressoor" / "skills" / "compressoor" / "scripts" / "launch_codex_compressoor.py",
]
INSTALLER_PATHS = [
    ROOT / "skills" / "compressoor" / "scripts" / "install_codex_compressoor.py",
    ROOT / "plugins" / "compressoor" / "skills" / "compressoor" / "scripts" / "install_codex_compressoor.py",
]


class PluginDefaultsTests(unittest.TestCase):
    def test_default_prompt_requires_compressoor_by_default(self) -> None:
        payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        prompts = payload["interface"]["defaultPrompt"]
        self.assertEqual(len(prompts), 1)
        prompt = prompts[0]
        self.assertIn("Use $compressoor by default", prompt)
        self.assertIn("apply to all agents and sub-agents", prompt)
        self.assertIn("avoid narrating each step", prompt)
        self.assertIn("Tool calls first", prompt)
        self.assertIn("take that tool action before any optional progress or summary text", prompt)
        self.assertIn("do not send any human-readable pre-tool status message first", prompt)
        self.assertIn("Do not send progress updates unless the environment requires one", prompt)
        self.assertIn("do not send routine plaintext progress updates", prompt)
        self.assertIn("emit only the true encoder-produced packed CCM1/template context instead of human-readable status text or a hand-written packed-looking paraphrase", prompt)
        self.assertIn("Required updates, reusable memory, and handoffs must use compressoor methods rather than plaintext", prompt)
        self.assertIn("encode it with compressoor, store the encoded context", prompt)
        self.assertIn("replace the verbose form with CCM1 or compact envelopes as the new active context by default", prompt)
        self.assertIn("Keep final summaries extremely terse", prompt)

    def test_skill_docs_require_tool_first_and_encoded_context_storage(self) -> None:
        skill_paths = [
            ROOT / "skills" / "compressoor" / "SKILL.md",
            ROOT / "plugins" / "compressoor" / "skills" / "compressoor" / "SKILL.md",
        ]
        for path in skill_paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("mandatory for all agents and sub-agents operating with compressoor enabled", text)
                self.assertIn("prefer taking the next relevant tool action before sending any optional outward message", text)
                self.assertIn("Never send an optional progress message before a tool call when a tool can materially advance the task.", text)
                self.assertIn("Never send a human-readable pre-tool status message when a tool can materially advance the task.", text)
                self.assertIn("Tool calls first. If a tool can advance the task, take that tool action before any optional progress or summary text.", text)
                self.assertIn("Do not send a human-readable status message before a tool call when the tool can advance the task.", text)
                self.assertIn("If a progress update is unavoidable, encode it with the compressoor protocol instead of sending plaintext status.", text)
                self.assertIn("If a progress update is unavoidable, generate it with the compressoor encoder rather than hand-writing a packed-looking string.", text)
                self.assertIn("Never bypass compressoor for reusable memory, handoffs, or required progress payloads.", text)
                self.assertIn("store the encoded context", text)

    def test_agent_yaml_prompts_enforce_required_only_encoded_updates(self) -> None:
        for path in AGENT_YAML_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("apply to all agents and sub-agents", text)
                self.assertIn("Tool calls first", text)
                self.assertIn("Do not send progress updates unless the environment requires one", text)
                self.assertIn("do not send routine plaintext progress updates", text)
                self.assertIn("emit only the true encoder-produced packed CCM1/template context", text)
                self.assertIn("hand-written packed-looking paraphrase", text)
                self.assertIn("do not send any human-readable pre-tool status message first", text)
                self.assertIn("Required updates, reusable memory, and handoffs must use compressoor methods rather than plaintext", text)

    def test_launchers_exist_for_pre_hook_session_bootstrap(self) -> None:
        for path in LAUNCHER_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Launch interactive Codex with a packed compressoor bootstrap prompt.", text)
                self.assertIn("SESSION_POLICY_TEXT", text)
                self.assertIn("SESSION_POLICY =", text)
                self.assertIn("Do not send any human-readable status message before a tool call", text)
                self.assertIn("os.execvp", text)

    def test_installers_exist_for_default_hook_and_agents_enforcement(self) -> None:
        for path in INSTALLER_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Install compressoor's default Codex policy into AGENTS, hooks, and config files.", text)
                self.assertIn("render_hooks_config", text)
                self.assertIn("enable_hooks_feature", text)

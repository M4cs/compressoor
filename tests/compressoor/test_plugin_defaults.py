from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = ROOT / "plugins" / "compressoor" / ".codex-plugin" / "plugin.json"
CLAUDE_PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
CLAUDE_MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_AGENT = ROOT / ".claude" / "agents" / "compressoor.md"
CLAUDE_COMMAND = ROOT / ".claude" / "commands" / "compressoor.md"
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
    def test_default_prompt_is_explicit_only(self) -> None:
        payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        prompts = payload["interface"]["defaultPrompt"]
        self.assertEqual(len(prompts), 1)
        prompt = prompts[0]
        self.assertIn("Compressoor session mode is active", prompt)
        self.assertIn("call them silently", prompt)
        self.assertIn("Never send acknowledgements, commentary, progress updates", prompt)
        self.assertIn("before, between, or during tool calls", prompt)
        self.assertIn("Finish the current tool loop first", prompt)
        self.assertIn("extreme minimalism", prompt)
        self.assertIn("Explain only failures, blockers, or changed files", prompt)
        self.assertLess(len(prompt), 620)

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
                self.assertIn("Never send any message before the current tool loop is complete.", text)
                self.assertIn("Never send acknowledgements, commentary, or status text before, between, or during tool calls.", text)
                self.assertIn("Never interrupt an active tool-gathering or tool-execution loop with plaintext status.", text)
                self.assertIn("Call tools silently whenever tools can advance the task.", text)
                self.assertIn("Tool calls first. If a tool can advance the task, take that tool action before any message.", text)
                self.assertIn("Do not send a human-readable status message before a tool call when the tool can advance the task.", text)
                self.assertIn("complete that tool loop before sending explanation", text)
                self.assertIn("Do not emit progress updates.", text)
                self.assertIn("Never bypass compressoor for reusable memory or handoffs.", text)
                self.assertIn("store the encoded context", text)

    def test_agent_yaml_prompts_are_explicit_only(self) -> None:
        for path in AGENT_YAML_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Compressoor session mode is active", text)
                self.assertIn("call them silently", text)
                self.assertIn("Never send acknowledgements, commentary, progress updates", text)
                self.assertIn("before, between, or during tool calls", text)
                self.assertIn("Finish the current tool loop first", text)
                self.assertIn("extreme minimalism", text)
                self.assertIn("Explain only failures, blockers, or changed files", text)
                self.assertIn("allow_implicit_invocation: false", text)

    def test_claude_plugin_manifest_is_present_and_explicit_only(self) -> None:
        payload = json.loads(CLAUDE_PLUGIN_JSON.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "compressoor")
        self.assertIn("Explicit-use context compaction", payload["description"])
        self.assertEqual(payload["author"]["name"], "Max")

    def test_claude_marketplace_points_at_repo_root(self) -> None:
        payload = json.loads(CLAUDE_MARKETPLACE_JSON.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "compressoor")
        self.assertEqual(len(payload["plugins"]), 1)
        plugin = payload["plugins"][0]
        self.assertEqual(plugin["name"], "compressoor")
        self.assertEqual(plugin["source"], "./")
        self.assertEqual(plugin["category"], "productivity")
        self.assertIn("default runtime policy", plugin["description"])

    def test_claude_subagent_is_explicit_only(self) -> None:
        text = CLAUDE_AGENT.read_text(encoding="utf-8")
        self.assertIn("Explicit-use context compaction specialist", text)
        self.assertIn("Do not treat it as a default runtime policy", text)
        self.assertIn("call tools silently whenever tools can advance the task", text)
        self.assertIn("never send any message before the current tool loop is complete", text)
        self.assertIn("never send acknowledgements, commentary, or status text before, between, or during tool calls", text)
        self.assertIn("packed `CCM1` block", text)
        self.assertIn("say only what changed, or note failures/blockers when needed", text)
        self.assertIn("Do not turn this subagent into a session-wide voice", text)

    def test_claude_command_routes_into_explicit_compaction(self) -> None:
        text = CLAUDE_COMMAND.read_text(encoding="utf-8")
        self.assertIn("Use the `compressoor` subagent", text)
        self.assertIn("Compressoor is explicit-use only", text)
        self.assertIn("pack, unpack, benchmark, or rewrite durable reusable context", text)
        self.assertIn("call tools silently whenever tools can advance the task", text)
        self.assertIn("never send any message before the current tool loop is complete", text)
        self.assertIn("never send acknowledgements, commentary, or status text before, between, or during tool calls", text)
        self.assertIn("return the shortest correct result only", text)
        self.assertIn("explain only failures, blockers, or changed files when needed", text)
        self.assertIn("User arguments: $ARGUMENTS", text)

    def test_launchers_exist_for_session_prompt_bootstrap(self) -> None:
        for path in LAUNCHER_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Launch interactive Codex with an explicit compressoor system prompt.", text)
                self.assertIn("build_bootstrap", text)
                self.assertIn("has_compressoor_policy", text)
                self.assertIn("os.execvp", text)

    def test_installers_exist_for_agents_and_session_hooks(self) -> None:
        for path in INSTALLER_PATHS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("Install compressoor's explicit-use notes into AGENTS and hooks files.", text)
                self.assertIn("render_hooks_config", text)
                self.assertIn("SessionStart", text)
                self.assertIn("SessionResume", text)

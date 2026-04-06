from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = ROOT / "plugins" / "compressoor" / ".codex-plugin" / "plugin.json"


class PluginDefaultsTests(unittest.TestCase):
    def test_default_prompt_requires_compressoor_by_default(self) -> None:
        payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        prompts = payload["interface"]["defaultPrompt"]
        self.assertEqual(len(prompts), 1)
        prompt = prompts[0]
        self.assertIn("Use $compressoor by default", prompt)
        self.assertIn("avoid narrating each step", prompt)
        self.assertIn("Do not send routine plaintext progress updates", prompt)
        self.assertIn("emit the true packed CCM1/template context instead of human-readable status text", prompt)
        self.assertIn("replace the verbose form with CCM1 or compact envelopes as the new active context by default", prompt)
        self.assertIn("Keep final summaries extremely terse", prompt)

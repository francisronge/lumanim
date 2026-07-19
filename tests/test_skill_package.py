from __future__ import annotations

import hashlib
import unittest

from _load import SKILL


class SkillPackageTests(unittest.TestCase):
    def test_portable_skill_shape(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name: lumanim$")
        self.assertRegex(text, r"(?m)^description: .+$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertRegex(text, r"(?m)^license: MIT$")
        nested = [path for path in SKILL.rglob("SKILL.md") if path != SKILL / "SKILL.md"]
        self.assertEqual(nested, [])

    def test_skill_ships_no_stylesheet_or_generated_files(self):
        forbidden = [
            path
            for path in SKILL.rglob("*")
            if path.is_file() and (path.suffix == ".css" or path.suffix == ".pyc" or "__pycache__" in path.parts)
        ]
        self.assertEqual(forbidden, [])

    def test_embedded_teach_contract_matches_declared_hash(self):
        contract = SKILL / "references" / "teach" / "TEACH-CONTRACT.md"
        actual = hashlib.sha256(contract.read_bytes()).hexdigest()
        provenance = (SKILL / "references" / "PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn(actual, provenance)

    def test_live_client_scopes_multiple_visual_experiences(self):
        client = (SKILL / "assets" / "lumanim-live.js").read_text(encoding="utf-8")
        self.assertIn("querySelectorAll", client)
        self.assertIn("data-lumanim-experience", client)
        self.assertIn("status.visual_id !== visualId", client)

    def test_no_personal_paths_or_common_secret_markers(self):
        markers = (
            "/" + "Users" + "/",
            "francis" + "ronge",
            "gh" + "p_",
            "github_" + "pat_",
            "PRIVATE" + " KEY",
        )
        findings = []
        for path in SKILL.rglob("*"):
            if path.is_file():
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if any(marker in text for marker in markers):
                    findings.append(path)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()

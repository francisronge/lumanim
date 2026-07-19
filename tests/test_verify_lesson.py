from __future__ import annotations

import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from _load import EXAMPLE, load_script

verify = load_script("verify_lesson")


class VerifyLessonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = shutil.copytree(EXAMPLE, Path(self.temp.name) / "lesson")

    def tearDown(self):
        self.temp.cleanup()

    def verify_without_ffprobe(self):
        with mock.patch.object(verify, "inspect_mp4"):
            return verify.verify_workspace(self.workspace)

    def test_valid_example_passes_structural_checks(self):
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_scene_hash_mismatch_fails(self):
        scene = self.workspace / "assets" / "manim" / "0001-ship-of-theseus" / "scene.py"
        scene.write_text(scene.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self.assertTrue(any("scene_sha256" in error for error in self.verify_without_ffprobe()))

    def test_reduced_motion_cannot_hide_fallback(self):
        css = self.workspace / "assets" / "paradoxes-dark.css"
        css.write_text(css.read_text(encoding="utf-8") + "\n@media (prefers-reduced-motion: reduce) { video { display: none; } }\n", encoding="utf-8")
        self.assertTrue(any("hides the fallback video" in error for error in self.verify_without_ffprobe()))

    def test_declared_reference_must_be_linked(self):
        html = self.workspace / "lessons" / "0001-ship-of-theseus.html"
        text = html.read_text(encoding="utf-8").replace(
            'href="../reference/identity-claims.html"',
            'href="#identity-claims"',
        )
        html.write_text(text, encoding="utf-8")
        self.assertTrue(any("does not link declared reference" in error for error in self.verify_without_ffprobe()))

    def test_local_query_string_fails(self):
        html = self.workspace / "lessons" / "0001-ship-of-theseus.html"
        text = html.read_text(encoding="utf-8").replace("paradoxes-dark.css", "paradoxes-dark.css?v=1")
        html.write_text(text, encoding="utf-8")
        self.assertTrue(any("query strings" in error for error in self.verify_without_ffprobe()))


if __name__ == "__main__":
    unittest.main()

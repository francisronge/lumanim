from __future__ import annotations

import json
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

    def make_two_visual_lesson(self):
        lesson_id = "0001-ship-of-theseus"
        root = self.workspace / "assets" / "manim" / lesson_id
        original = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        visuals = []
        for visual_id in ("gradual-replacement", "rival-reassembly"):
            target = root / "visuals" / visual_id
            target.mkdir(parents=True)
            for name in ("scene.py", "poster.png", "fallback.mp4"):
                shutil.copy2(root / name, target / name)
            shutil.copytree(root / "inspection", target / "inspection")
            visual = {
                key: original[key]
                for key in ("scene_class", "live_scene_class", "render", "live", "inspection")
            }
            visual.update({"visual_id": visual_id, "bundle": f"visuals/{visual_id}"})
            if visual_id == "rival-reassembly":
                visual["live"] = {"enabled": False}
            visuals.append(visual)
        manifest = {
            "schema_version": 2,
            "lesson_id": lesson_id,
            "references": original["references"],
            "manimgl": original["manimgl"],
            "visuals": visuals,
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        lesson = self.workspace / "lessons" / f"{lesson_id}.html"
        html = lesson.read_text(encoding="utf-8")
        html = html.replace(
            'class="lumanim-stage" data-lumanim-stage',
            'class="lumanim-stage" data-lumanim-experience="gradual-replacement" data-lumanim-stage',
        ).replace(
            f"assets/manim/{lesson_id}/poster.png",
            f"assets/manim/{lesson_id}/visuals/gradual-replacement/poster.png",
        ).replace(
            f"assets/manim/{lesson_id}/fallback.mp4",
            f"assets/manim/{lesson_id}/visuals/gradual-replacement/fallback.mp4",
        )
        second = (
            f'<video controls poster="../assets/manim/{lesson_id}/visuals/rival-reassembly/poster.png">'
            f'<source src="../assets/manim/{lesson_id}/visuals/rival-reassembly/fallback.mp4" '
            'type="video/mp4"></video>'
        )
        lesson.write_text(html.replace("</main>", f"{second}</main>"), encoding="utf-8")
        return root, lesson

    def test_valid_example_passes_structural_checks(self):
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_valid_two_visual_lesson_passes_structural_checks(self):
        self.make_two_visual_lesson()
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_each_visual_fallback_must_be_linked(self):
        _, lesson = self.make_two_visual_lesson()
        html = lesson.read_text(encoding="utf-8").replace(
            '<source src="../assets/manim/0001-ship-of-theseus/visuals/rival-reassembly/fallback.mp4" '
            'type="video/mp4">',
            "",
        )
        lesson.write_text(html, encoding="utf-8")
        errors = self.verify_without_ffprobe()
        self.assertTrue(any("rival-reassembly: HTML does not link fallback.mp4" in error for error in errors))

    def test_duplicate_visual_id_fails(self):
        root, _ = self.make_two_visual_lesson()
        path = root / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["visuals"][1]["visual_id"] = manifest["visuals"][0]["visual_id"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertTrue(any("duplicate visual_id" in error for error in self.verify_without_ffprobe()))

    def test_visual_bundle_cannot_escape_lesson(self):
        root, _ = self.make_two_visual_lesson()
        path = root / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["visuals"][1]["bundle"] = "../../outside"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertTrue(any("escapes the lesson bundle" in error for error in self.verify_without_ffprobe()))

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

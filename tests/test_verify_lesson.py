from __future__ import annotations

import base64
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from _load import EXAMPLE, load_script

package = load_script("package_lesson")
verify = load_script("verify_lesson")


class VerifyLessonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = shutil.copytree(EXAMPLE, Path(self.temp.name) / "lesson")
        for source in (self.workspace / "lessons").glob("*.source.html"):
            output = source.with_name(source.name.replace(".source.html", ".html"))
            shutil.copy2(source, output)
            source.unlink()

    def tearDown(self):
        self.temp.cleanup()

    def verify_without_ffprobe(self):
        with mock.patch.object(verify, "inspect_mp4"):
            return verify.verify_workspace(self.workspace)

    def package_other_lessons(self, lesson_id):
        for candidate in package.lesson_ids(self.workspace, []):
            if candidate != lesson_id:
                package.package_lesson(self.workspace, candidate)

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
        for lesson_id in package.lesson_ids(self.workspace, []):
            package.package_lesson(self.workspace, lesson_id)
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_valid_two_visual_lesson_passes_structural_checks(self):
        _, lesson = self.make_two_visual_lesson()
        package.package_lesson(self.workspace, lesson.stem)
        self.package_other_lessons(lesson.stem)
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_unpacked_lesson_fails_with_packaging_instruction(self):
        errors = self.verify_without_ffprobe()
        self.assertTrue(any("run package_lesson.py" in error for error in errors))

    def test_exact_standalone_media_passes_structural_checks(self):
        root, lesson = self.make_two_visual_lesson()
        html = lesson.read_text(encoding="utf-8")
        css_path = self.workspace / "assets" / "paradoxes.css"
        html = html.replace(
            '<link rel="stylesheet" href="../assets/paradoxes.css">',
            '<meta name="lumanim-packaging" content="standalone">'
            f'<style>{css_path.read_text(encoding="utf-8")}</style>',
        )
        for visual_id in ("gradual-replacement", "rival-reassembly"):
            visual = root / "visuals" / visual_id
            poster = base64.b64encode((visual / "poster.png").read_bytes()).decode("ascii")
            fallback = base64.b64encode((visual / "fallback.mp4").read_bytes()).decode("ascii")
            relative = f"../assets/manim/0001-ship-of-theseus/visuals/{visual_id}"
            html = html.replace(f"{relative}/poster.png", f"data:image/png;base64,{poster}")
            html = html.replace(f"{relative}/fallback.mp4", f"data:video/mp4;base64,{fallback}")
        lesson.write_text(html, encoding="utf-8")
        self.package_other_lessons("0001-ship-of-theseus")
        self.assertEqual(self.verify_without_ffprobe(), [])

    def test_standalone_media_must_match_preserved_fallback(self):
        root, lesson = self.make_two_visual_lesson()
        html = lesson.read_text(encoding="utf-8")
        css_path = self.workspace / "assets" / "paradoxes.css"
        html = html.replace(
            '<link rel="stylesheet" href="../assets/paradoxes.css">',
            '<meta name="lumanim-packaging" content="standalone">'
            f'<style>{css_path.read_text(encoding="utf-8")}</style>',
        )
        visual_id = "gradual-replacement"
        relative = f"../assets/manim/0001-ship-of-theseus/visuals/{visual_id}"
        html = html.replace(f"{relative}/poster.png", "data:image/png;base64,YmFk")
        html = html.replace(f"{relative}/fallback.mp4", "data:video/mp4;base64,YmFk")
        lesson.write_text(html, encoding="utf-8")
        errors = self.verify_without_ffprobe()
        self.assertTrue(any(f"{visual_id}: HTML does not link fallback.mp4" in error for error in errors))
        self.assertTrue(any(f"{visual_id}: HTML does not link poster.png" in error for error in errors))

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
        css = self.workspace / "assets" / "paradoxes.css"
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
        text = html.read_text(encoding="utf-8").replace("paradoxes.css", "paradoxes.css?v=1")
        html.write_text(text, encoding="utf-8")
        self.assertTrue(any("query strings" in error for error in self.verify_without_ffprobe()))


if __name__ == "__main__":
    unittest.main()

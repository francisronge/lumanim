from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from _load import load_script

runtime = load_script("lumanim_runtime")


class RuntimeSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.lesson_id = "lesson-one"
        self.bundle = self.workspace / "assets" / "manim" / self.lesson_id
        self.bundle.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write_v2(self, live_ids=("first",)):
        visuals = []
        for visual_id in ("first", "second"):
            relative = f"visuals/{visual_id}"
            visual_bundle = self.bundle / relative
            visual_bundle.mkdir(parents=True)
            (visual_bundle / "scene.py").write_text("# trusted in tests\n", encoding="utf-8")
            visuals.append(
                {
                    "visual_id": visual_id,
                    "bundle": relative,
                    "live_scene_class": "LiveScene",
                    "live": {"enabled": visual_id in live_ids},
                }
            )
        manifest = {
            "schema_version": 2,
            "lesson_id": self.lesson_id,
            "manimgl": {"commit": "test"},
            "visuals": visuals,
        }
        (self.bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_explicit_visual_selection(self):
        self.write_v2(live_ids=("first", "second"))
        bundle, _, visual = runtime.resolve_live_visual(self.workspace, self.lesson_id, "second")
        self.assertEqual(visual["visual_id"], "second")
        self.assertEqual(bundle, (self.bundle / "visuals" / "second").resolve())

    def test_only_live_visual_is_selected_automatically(self):
        self.write_v2(live_ids=("second",))
        _, _, visual = runtime.resolve_live_visual(self.workspace, self.lesson_id)
        self.assertEqual(visual["visual_id"], "second")

    def test_multiple_live_visuals_require_selection(self):
        self.write_v2(live_ids=("first", "second"))
        with self.assertRaisesRegex(ValueError, "multiple live visuals"):
            runtime.resolve_live_visual(self.workspace, self.lesson_id)

    def test_unknown_visual_is_rejected(self):
        self.write_v2()
        with self.assertRaisesRegex(ValueError, "Unknown visual"):
            runtime.resolve_live_visual(self.workspace, self.lesson_id, "missing")

    def test_non_live_visual_is_rejected(self):
        self.write_v2()
        with self.assertRaisesRegex(ValueError, "does not declare live mode"):
            runtime.resolve_live_visual(self.workspace, self.lesson_id, "second")

    def test_schema_one_remains_supported(self):
        (self.bundle / "scene.py").write_text("# trusted in tests\n", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "lesson_id": self.lesson_id,
            "live_scene_class": "LiveScene",
            "live": {"enabled": True},
            "manimgl": {"commit": "test"},
        }
        (self.bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        bundle, _, visual = runtime.resolve_live_visual(self.workspace, self.lesson_id)
        self.assertEqual(bundle, self.bundle.resolve())
        self.assertEqual(visual["visual_id"], self.lesson_id)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from _load import EXAMPLE, load_script

package = load_script("package_lesson")
verify = load_script("verify_lesson")


class PackageLessonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = shutil.copytree(EXAMPLE, Path(self.temp.name) / "lesson")
        for source in (self.workspace / "lessons").glob("*.source.html"):
            output = source.with_name(source.name.replace(".source.html", ".html"))
            shutil.copy2(source, output)
            source.unlink()

    def tearDown(self):
        self.temp.cleanup()

    def test_package_is_self_contained_and_reproducible(self):
        lesson_id = "0001-ship-of-theseus"
        output = self.workspace / "lessons" / f"{lesson_id}.html"
        original = output.read_bytes()

        source, packaged = package.package_lesson(self.workspace, lesson_id)
        first = packaged.read_bytes()
        self.assertEqual(source.read_bytes(), original)
        self.assertIn(b'name="lumanim-packaging" content="standalone"', first)
        self.assertIn(b"data:video/mp4;base64,", first)
        self.assertIn(b"data:image/png;base64,", first)
        self.assertIn(b"<style data-lumanim-source=", first)
        self.assertIn(b"<script data-lumanim-source=", first)
        self.assertNotIn(b'<link rel="stylesheet"', first)
        self.assertNotIn(b'<script src="../assets/', first)
        self.assertNotIn(b'<source src="../assets/', first)

        package.package_lesson(self.workspace, lesson_id)
        self.assertEqual(packaged.read_bytes(), first)

        for candidate in package.lesson_ids(self.workspace, []):
            if candidate != lesson_id:
                package.package_lesson(self.workspace, candidate)
        with mock.patch.object(verify, "inspect_mp4"):
            self.assertEqual(verify.verify_workspace(self.workspace), [])

    def test_local_asset_cannot_escape_workspace(self):
        lesson_id = "0001-ship-of-theseus"
        output = self.workspace / "lessons" / f"{lesson_id}.html"
        output.write_text(
            output.read_text(encoding="utf-8").replace(
                "../assets/paradoxes.css",
                "../../../outside.css",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "escapes the workspace"):
            package.package_lesson(self.workspace, lesson_id)

    def test_course_index_can_be_packaged(self):
        source, output = package.package_page(self.workspace, self.workspace / "index.html")
        self.assertTrue(source.is_file())
        html = output.read_text(encoding="utf-8")
        self.assertIn('name="lumanim-packaging" content="standalone"', html)
        self.assertIn("<style data-lumanim-source=", html)
        self.assertNotIn('<link rel="stylesheet"', html)


if __name__ == "__main__":
    unittest.main()

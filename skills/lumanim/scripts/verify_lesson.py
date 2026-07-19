#!/usr/bin/env python3
"""Verify Lumanim lesson bundles without importing untrusted scene code."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from html.parser import HTMLParser
import json
import re
import shutil
import struct
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

PINNED_COMMIT = "6199a00d4c1b1127ebe45cb629c3f22538b10e13"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class LessonHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str, str]] = []
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.ids: set[str] = set()
        self.experience_ids: set[str] = set()
        self.video_controls = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        if values.get("id"):
            self.ids.add(values["id"])
        if values.get("data-lumanim-experience"):
            self.experience_ids.add(values["data-lumanim-experience"])
        for attribute in ("href", "src", "poster"):
            if values.get(attribute):
                self.references.append((tag, attribute, values[attribute]))
        if tag == "link" and "stylesheet" in values.get("rel", "").split():
            self.stylesheets.append(values.get("href", ""))
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "video" and "controls" in values:
            self.video_controls = True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_target(workspace: Path, page: Path, value: str) -> tuple[Path | None, str | None]:
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or parsed.netloc:
        return None, None
    if parsed.scheme or value.startswith("/"):
        return None, "must use a relative local path"
    if parsed.query:
        return None, "local paths must not contain query strings"
    target = page if not parsed.path else (page.parent / parsed.path).resolve()
    try:
        target.relative_to(workspace)
    except ValueError:
        return None, "local path escapes the teaching workspace"
    return target, None


def inspect_html(
    workspace: Path,
    lesson: Path,
    lesson_id: str,
    references: list[str],
    visuals: list[dict],
    errors: list[str],
) -> None:
    html = lesson.read_text(encoding="utf-8")
    parser = LessonHTML()
    try:
        parser.feed(html)
    except Exception as error:
        errors.append(f"{lesson_id}: HTML could not be parsed: {error}")
        return

    if not parser.stylesheets:
        errors.append(f"{lesson_id}: HTML has no workspace stylesheet")
    if not parser.video_controls:
        errors.append(f"{lesson_id}: fallback video lacks learner controls")

    resolved: dict[str, Path] = {}
    for tag, attribute, value in parser.references:
        target, problem = local_target(workspace, lesson, value)
        if problem:
            errors.append(f"{lesson_id}: {tag}[{attribute}] {value!r} {problem}")
            continue
        if target is None:
            continue
        resolved[value] = target
        fragment = urlsplit(value).fragment
        if target == lesson and fragment and fragment not in parser.ids:
            errors.append(f"{lesson_id}: missing in-page target #{fragment}")
        if not target.is_file() or target.stat().st_size == 0:
            errors.append(f"{lesson_id}: broken local reference {value!r}")

    linked_media = set(resolved.values())
    for visual in visuals:
        visual_id = visual["visual_id"]
        visual_bundle = visual["_bundle"]
        for name in ("fallback.mp4", "poster.png"):
            expected = visual_bundle / name
            if expected not in linked_media:
                errors.append(f"{lesson_id}/{visual_id}: HTML does not link {name}")

    live_visuals = [visual for visual in visuals if visual.get("live", {}).get("enabled")]
    if live_visuals:
        if not any(Path(urlsplit(value).path).name == "lumanim-live.js" for value in parser.scripts):
            errors.append(f"{lesson_id}: live lesson does not load lumanim-live.js")
    for visual in live_visuals:
        if visual.get("_schema_version") == 2 and visual["visual_id"] not in parser.experience_ids:
            errors.append(
                f"{lesson_id}/{visual['visual_id']}: live visual lacks matching "
                "data-lumanim-experience"
            )

    for relative in references:
        expected = (workspace / relative).resolve()
        if expected not in linked_media:
            errors.append(f"{lesson_id}: HTML does not link declared reference {relative}")

    if "ask" not in html.lower() or "agent" not in html.lower():
        errors.append(f"{lesson_id}: HTML lacks the /teach follow-up reminder")

    for stylesheet in parser.stylesheets:
        target = resolved.get(stylesheet)
        if target and target.is_file():
            css = target.read_text(encoding="utf-8")
            reduced_motion_hides_video = re.search(
                r"prefers-reduced-motion[\s\S]{0,500}\bvideo\b[\s\S]{0,200}display\s*:\s*none",
                css,
                re.IGNORECASE | re.DOTALL,
            )
            if reduced_motion_hides_video:
                errors.append(f"{lesson_id}: reduced-motion CSS hides the fallback video")


def inspect_png(path: Path, expected_resolution: list[int], lesson_id: str, errors: list[str]) -> None:
    with path.open("rb") as source:
        header = source.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE:
        errors.append(f"{lesson_id}: poster.png is not a valid PNG")
        return
    width, height = struct.unpack(">II", header[16:24])
    if [width, height] != expected_resolution:
        errors.append(
            f"{lesson_id}: poster resolution {[width, height]} does not match render {expected_resolution}"
        )


def inspect_mp4(path: Path, render: dict, lesson_id: str, errors: list[str]) -> None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        errors.append(f"{lesson_id}: ffprobe is required to verify fallback.mp4")
        return
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(f"{lesson_id}: ffprobe rejected fallback.mp4")
        return
    try:
        stream = json.loads(result.stdout)["streams"][0]
        actual_resolution = [int(stream["width"]), int(stream["height"])]
        actual_fps = float(Fraction(stream["r_frame_rate"]))
    except (KeyError, IndexError, ValueError, ZeroDivisionError, json.JSONDecodeError):
        errors.append(f"{lesson_id}: fallback.mp4 has unreadable video metadata")
        return
    if stream.get("codec_name") != "h264" or stream.get("pix_fmt") != "yuv420p":
        errors.append(f"{lesson_id}: fallback.mp4 must be H.264 yuv420p")
    if actual_resolution != render["resolution"]:
        errors.append(f"{lesson_id}: fallback resolution {actual_resolution} does not match manifest")
    if abs(actual_fps - float(render["fps"])) > 0.01:
        errors.append(f"{lesson_id}: fallback frame rate {actual_fps:g} does not match manifest")

    data = path.read_bytes()
    moov = data.find(b"moov")
    mdat = data.find(b"mdat")
    if moov < 0 or mdat < 0 or moov > mdat:
        errors.append(f"{lesson_id}: fallback.mp4 is not web-optimized with faststart")


def normalize_manifest(bundle: Path, manifest: dict, errors: list[str]) -> tuple[str | None, list[str], list[dict]]:
    lesson_id = manifest.get("lesson_id")
    if not isinstance(lesson_id, str) or not SLUG.fullmatch(lesson_id):
        errors.append(f"{lesson_id}: invalid lesson_id")
        return None, [], []
    if lesson_id != bundle.name:
        errors.append(f"{lesson_id}: lesson_id must match bundle directory {bundle.name}")

    references = manifest.get("references", [])
    if not isinstance(references, list) or not all(isinstance(item, str) for item in references):
        errors.append(f"{lesson_id}: references must be a list of paths")
        references = []

    schema_version = manifest.get("schema_version")
    if schema_version == 1:
        visual = dict(manifest)
        visual.update(
            {
                "visual_id": lesson_id,
                "_bundle": bundle,
                "_schema_version": 1,
            }
        )
        return lesson_id, references, [visual]
    if schema_version != 2:
        errors.append(f"{lesson_id}: unsupported or missing schema_version")
        return lesson_id, references, []

    declared = manifest.get("visuals")
    if not isinstance(declared, list) or not declared:
        errors.append(f"{lesson_id}: schema 2 requires at least one visual")
        return lesson_id, references, []

    visuals: list[dict] = []
    seen_ids: set[str] = set()
    seen_bundles: set[Path] = set()
    bundle_root = bundle.resolve()
    for index, raw in enumerate(declared):
        if not isinstance(raw, dict):
            errors.append(f"{lesson_id}: visuals[{index}] must be an object")
            continue
        visual_id = raw.get("visual_id")
        label = f"{lesson_id}/{visual_id}"
        if not isinstance(visual_id, str) or not SLUG.fullmatch(visual_id):
            errors.append(f"{label}: invalid visual_id")
            continue
        if visual_id in seen_ids:
            errors.append(f"{label}: duplicate visual_id")
            continue
        seen_ids.add(visual_id)

        relative = raw.get("bundle")
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            errors.append(f"{label}: bundle must be a relative path")
            continue
        visual_bundle = (bundle / relative).resolve()
        try:
            visual_bundle.relative_to(bundle_root)
        except ValueError:
            errors.append(f"{label}: bundle path escapes the lesson bundle")
            continue
        if visual_bundle in seen_bundles:
            errors.append(f"{label}: duplicate bundle path")
            continue
        seen_bundles.add(visual_bundle)

        visual = dict(raw)
        visual.update(
            {
                "visual_id": visual_id,
                "_bundle": visual_bundle,
                "_schema_version": 2,
            }
        )
        visuals.append(visual)
    return lesson_id, references, visuals


def inspect_visual(workspace: Path, lesson_id: str, visual: dict, errors: list[str]) -> None:
    visual_id = visual["visual_id"]
    label = lesson_id if visual.get("_schema_version") == 1 else f"{lesson_id}/{visual_id}"
    bundle = visual["_bundle"]
    scene = bundle / "scene.py"
    poster = bundle / "poster.png"
    fallback = bundle / "fallback.mp4"
    missing = False
    for path in (scene, poster, fallback):
        if not path.is_file() or path.stat().st_size == 0:
            try:
                relative = path.relative_to(workspace)
            except ValueError:
                relative = path
            errors.append(f"{label}: missing or empty {relative}")
            missing = True
    if missing:
        return

    source = scene.read_text(encoding="utf-8")
    if not re.search(r"^from manimlib import \*", source, re.MULTILINE):
        errors.append(f"{label}: scene.py does not import the canonical manimlib")
    if not isinstance(visual.get("scene_class"), str) or not visual.get("scene_class"):
        errors.append(f"{label}: scene_class is missing")

    live = visual.get("live")
    if not isinstance(live, dict):
        errors.append(f"{label}: live must be an object")
        live = {}
    if live.get("enabled") and not visual.get("live_scene_class"):
        errors.append(f"{label}: live_scene_class is missing")

    inspection = visual.get("inspection")
    if not isinstance(inspection, dict):
        errors.append(f"{label}: inspection must be an object")
        inspection = {}
    if inspection.get("reviewed") is not True:
        errors.append(f"{label}: inspection.reviewed must be true")
    frames = inspection.get("frames", [])
    if not isinstance(frames, list) or not frames:
        errors.append(f"{label}: no inspection frames recorded")
        frames = []
    for relative in frames:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            errors.append(f"{label}: missing inspection frame {relative}")
            continue
        frame = (bundle / relative).resolve()
        try:
            frame.relative_to(bundle.resolve())
        except ValueError:
            errors.append(f"{label}: inspection frame escapes the visual bundle: {relative}")
            continue
        if not frame.is_file() or frame.stat().st_size == 0:
            errors.append(f"{label}: missing inspection frame {relative}")

    render = visual.get("render", {})
    required_render = (
        "command",
        "resolution",
        "fps",
        "seed",
        "scene_sha256",
        "fallback_sha256",
        "poster_sha256",
    )
    render_valid = isinstance(render, dict)
    if not render_valid:
        errors.append(f"{label}: render must be an object")
        render = {}
    for field in required_render:
        if field not in render:
            errors.append(f"{label}: render.{field} is missing")
            render_valid = False
    resolution = render.get("resolution")
    if not isinstance(resolution, list) or len(resolution) != 2 or not all(
        isinstance(number, int) and number > 0 for number in resolution
    ):
        errors.append(f"{label}: render.resolution must contain two positive integers")
        render_valid = False
    if not render_valid:
        return

    for name, path in (("scene", scene), ("fallback", fallback), ("poster", poster)):
        actual = sha256(path)
        if render[f"{name}_sha256"] != actual:
            errors.append(f"{label}: render.{name}_sha256 does not match {path.name}")

    inspect_png(poster, resolution, label, errors)
    inspect_mp4(fallback, render, label, errors)


def check_bundle(workspace: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    bundle = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{manifest_path}: invalid JSON: {error}"]

    lesson_id, references, visuals = normalize_manifest(bundle, manifest, errors)
    if lesson_id is None:
        return errors

    manimgl = manifest.get("manimgl", {})
    if manimgl.get("repository") != "https://github.com/3b1b/manim":
        errors.append(f"{lesson_id}: canonical ManimGL repository is missing")
    if manimgl.get("commit") != PINNED_COMMIT:
        errors.append(f"{lesson_id}: ManimGL commit must be {PINNED_COMMIT}")

    lesson = workspace / "lessons" / f"{lesson_id}.html"
    if not lesson.is_file() or lesson.stat().st_size == 0:
        errors.append(f"{lesson_id}: missing or empty lessons/{lesson_id}.html")
    for visual in visuals:
        inspect_visual(workspace, lesson_id, visual, errors)
    if lesson.is_file() and visuals:
        inspect_html(workspace, lesson, lesson_id, references, visuals, errors)
    return errors


def verify_workspace(workspace: Path) -> list[str]:
    workspace = workspace.expanduser().resolve()
    manifests = sorted((workspace / "assets" / "manim").glob("*/manifest.json"))
    if not manifests:
        return ["no Lumanim manifests found"]
    return [error for manifest in manifests for error in check_bundle(workspace, manifest)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    errors = verify_workspace(workspace)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    manifests = list((workspace / "assets" / "manim").glob("*/manifest.json"))
    visual_count = 0
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        visual_count += len(manifest.get("visuals", [])) if manifest.get("schema_version") == 2 else 1
    print(
        f"PASS: verified {len(manifests)} Lumanim lesson bundle(s), "
        f"{visual_count} visual bundle(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

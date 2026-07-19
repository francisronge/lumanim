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


class LessonHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str, str]] = []
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []
        self.ids: set[str] = set()
        self.video_controls = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        if values.get("id"):
            self.ids.add(values["id"])
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


def inspect_html(workspace: Path, lesson: Path, manifest: dict, errors: list[str]) -> None:
    lesson_id = manifest["lesson_id"]
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

    bundle = workspace / "assets" / "manim" / lesson_id
    expected_media = {bundle / "fallback.mp4", bundle / "poster.png"}
    linked_media = set(resolved.values())
    for expected in expected_media:
        if expected not in linked_media:
            errors.append(f"{lesson_id}: HTML does not link {expected.name}")

    if manifest.get("live", {}).get("enabled"):
        if not any(Path(urlsplit(value).path).name == "lumanim-live.js" for value in parser.scripts):
            errors.append(f"{lesson_id}: live lesson does not load lumanim-live.js")

    for relative in manifest.get("references", []):
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


def check_bundle(workspace: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    bundle = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{manifest_path}: invalid JSON: {error}"]

    lesson_id = manifest.get("lesson_id", bundle.name)
    if manifest.get("schema_version") != 1:
        errors.append(f"{lesson_id}: unsupported or missing schema_version")
    if lesson_id != bundle.name:
        errors.append(f"{lesson_id}: lesson_id must match bundle directory {bundle.name}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(lesson_id)):
        errors.append(f"{lesson_id}: invalid lesson_id")

    lesson = workspace / "lessons" / f"{lesson_id}.html"
    scene = bundle / "scene.py"
    poster = bundle / "poster.png"
    fallback = bundle / "fallback.mp4"
    required = [scene, poster, fallback, lesson]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"{lesson_id}: missing or empty {path.relative_to(workspace)}")
    if errors:
        return errors

    source = scene.read_text(encoding="utf-8")
    if not re.search(r"^from manimlib import \*", source, re.MULTILINE):
        errors.append(f"{lesson_id}: scene.py does not import the canonical manimlib")

    manimgl = manifest.get("manimgl", {})
    if manimgl.get("repository") != "https://github.com/3b1b/manim":
        errors.append(f"{lesson_id}: canonical ManimGL repository is missing")
    if manimgl.get("commit") != PINNED_COMMIT:
        errors.append(f"{lesson_id}: ManimGL commit must be {PINNED_COMMIT}")

    inspection = manifest.get("inspection", {})
    if inspection.get("reviewed") is not True:
        errors.append(f"{lesson_id}: inspection.reviewed must be true")
    frames = inspection.get("frames", [])
    if not frames:
        errors.append(f"{lesson_id}: no inspection frames recorded")
    for relative in frames:
        frame = bundle / relative
        if not frame.is_file() or frame.stat().st_size == 0:
            errors.append(f"{lesson_id}: missing inspection frame {relative}")

    render = manifest.get("render", {})
    for field in ("command", "resolution", "fps", "seed", "scene_sha256", "fallback_sha256", "poster_sha256"):
        if field not in render:
            errors.append(f"{lesson_id}: render.{field} is missing")
    resolution = render.get("resolution")
    if not isinstance(resolution, list) or len(resolution) != 2 or not all(isinstance(n, int) and n > 0 for n in resolution):
        errors.append(f"{lesson_id}: render.resolution must contain two positive integers")
    if errors:
        return errors

    for name, path in (("scene", scene), ("fallback", fallback), ("poster", poster)):
        actual = sha256(path)
        if render[f"{name}_sha256"] != actual:
            errors.append(f"{lesson_id}: render.{name}_sha256 does not match {path.name}")

    inspect_html(workspace, lesson, manifest, errors)
    inspect_png(poster, resolution, lesson_id, errors)
    inspect_mp4(fallback, render, lesson_id, errors)
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
    count = len(list((workspace / "assets" / "manim").glob("*/manifest.json")))
    print(f"PASS: verified {count} Lumanim lesson bundle(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

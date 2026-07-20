#!/usr/bin/env python3
"""Package Lumanim lessons as self-contained, direct-file-safe HTML."""

from __future__ import annotations

import argparse
import base64
from html import escape
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit


PACKAGING_META = '<meta name="lumanim-packaging" content="standalone">'
MEDIA_ATTRIBUTES = {
    "audio": ("src",),
    "embed": ("src",),
    "img": ("src",),
    "input": ("src",),
    "object": ("data",),
    "source": ("src",),
    "track": ("src",),
    "video": ("poster", "src"),
}
CSS_URL = re.compile(
    r"url\(\s*(?P<quote>['\"]?)(?P<value>.*?)(?P=quote)\s*\)",
    re.IGNORECASE,
)


class LessonAssets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: list[tuple[str, str]] = []
        self.scripts: list[tuple[str, str]] = []
        self.media: set[str] = set()
        self.packaging = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        raw = self.get_starttag_text()
        if tag == "meta" and values.get("name") == "lumanim-packaging":
            self.packaging = values.get("content", "")
        if tag == "link" and "stylesheet" in values.get("rel", "").split():
            if values.get("href"):
                self.stylesheets.append((raw, values["href"]))
        if tag == "script" and values.get("src"):
            self.scripts.append((raw, values["src"]))
        for attribute in MEDIA_ATTRIBUTES.get(tag, ()):
            if values.get(attribute):
                self.media.add(values[attribute])


def _local_path(workspace: Path, owner: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if (
        not value
        or value.startswith("#")
        or parsed.scheme in {"data", "http", "https", "mailto", "tel"}
        or parsed.netloc
    ):
        return None
    if parsed.scheme or value.startswith("/"):
        raise ValueError(f"local asset must use a relative path: {value!r}")
    if parsed.query:
        raise ValueError(f"local asset must not contain a query string: {value!r}")
    target = (owner.parent / parsed.path).resolve()
    try:
        target.relative_to(workspace)
    except ValueError as error:
        raise ValueError(f"local asset escapes the workspace: {value!r}") from error
    if not target.is_file() or target.stat().st_size == 0:
        raise ValueError(f"missing or empty local asset: {value!r}")
    return target


def _media_type(path: Path) -> str:
    known = {
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".mp4": "video/mp4",
        ".svg": "image/svg+xml",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    return known.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _data_uri(path: Path, payload: bytes | None = None) -> str:
    encoded = base64.b64encode(path.read_bytes() if payload is None else payload).decode("ascii")
    return f"data:{_media_type(path)};base64,{encoded}"


def _package_css(path: Path, workspace: Path, stack: tuple[Path, ...] = ()) -> str:
    resolved = path.resolve()
    if resolved in stack:
        chain = " -> ".join(item.name for item in (*stack, resolved))
        raise ValueError(f"cyclic CSS asset reference: {chain}")
    css = resolved.read_text(encoding="utf-8")

    def replace_url(match: re.Match[str]) -> str:
        value = match.group("value").strip()
        asset = _local_path(workspace, resolved, value)
        if asset is None:
            return match.group(0)
        if asset.suffix.lower() == ".css":
            nested = _package_css(asset, workspace, (*stack, resolved)).encode("utf-8")
            return f'url("{_data_uri(asset, nested)}")'
        return f'url("{_data_uri(asset)}")'

    return CSS_URL.sub(replace_url, css)


def _without_attribute(raw_tag: str, name: str) -> str:
    attribute = re.compile(
        rf"\s+{re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        re.IGNORECASE,
    )
    return attribute.sub("", raw_tag, count=1)


def _add_source_marker(raw_tag: str, source: str) -> str:
    marker = f' data-lumanim-source="{escape(source, quote=True)}"'
    if raw_tag.endswith("/>"):
        return raw_tag[:-2] + marker + ">"
    return raw_tag[:-1] + marker + ">"


def package_html(source: str, source_path: Path, workspace: Path) -> str:
    parser = LessonAssets()
    parser.feed(source)
    if parser.packaging == "standalone":
        raise ValueError(f"source is already packaged: {source_path}")

    packaged = source
    for raw_tag, value in parser.stylesheets:
        target = _local_path(workspace, source_path, value)
        if target is None:
            continue
        css = _package_css(target, workspace)
        replacement = (
            f'<style data-lumanim-source="{escape(value, quote=True)}">\n'
            f"{css}\n</style>"
        )
        packaged = packaged.replace(raw_tag, replacement, 1)

    for raw_tag, value in parser.scripts:
        target = _local_path(workspace, source_path, value)
        if target is None:
            continue
        javascript = target.read_text(encoding="utf-8").replace("</script", "<\\/script")
        opening = _without_attribute(raw_tag, "src")
        opening = _without_attribute(opening, "integrity")
        opening = _without_attribute(opening, "crossorigin")
        opening = _add_source_marker(opening, value)
        pattern = re.compile(re.escape(raw_tag) + r"\s*</script\s*>", re.IGNORECASE)
        packaged, count = pattern.subn(
            lambda _: f"{opening}\n{javascript}\n</script>",
            packaged,
            count=1,
        )
        if count != 1:
            raise ValueError(f"could not inline script element for {value!r}")

    for value in sorted(parser.media, key=len, reverse=True):
        target = _local_path(workspace, source_path, value)
        if target is None:
            continue
        uri = _data_uri(target)
        replaced = False
        for quote in ('"', "'"):
            needle = f"{quote}{value}{quote}"
            if needle in packaged:
                packaged = packaged.replace(needle, f"{quote}{uri}{quote}")
                replaced = True
        if not replaced:
            raise ValueError(f"could not inline media attribute for {value!r}")

    if re.search(
        r'<meta\s+[^>]*name=["\']lumanim-packaging["\']',
        packaged,
        re.IGNORECASE,
    ):
        packaged = re.sub(
            r'<meta\s+[^>]*name=["\']lumanim-packaging["\'][^>]*>',
            PACKAGING_META,
            packaged,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        packaged, count = re.subn(
            r"</head\s*>",
            f"  {PACKAGING_META}\n</head>",
            packaged,
            count=1,
            flags=re.IGNORECASE,
        )
        if count != 1:
            raise ValueError(f"lesson has no closing head element: {source_path}")
    return packaged


def package_page(workspace: Path, output: Path) -> tuple[Path, Path]:
    workspace = workspace.expanduser().resolve()
    output = output.resolve()
    try:
        output.relative_to(workspace)
    except ValueError as error:
        raise ValueError(f"page escapes the workspace: {output}") from error
    source = output.with_suffix(".source.html")
    if not source.exists():
        if not output.is_file() or output.stat().st_size == 0:
            raise ValueError(f"missing lesson HTML: {output}")
        current = LessonAssets()
        current.feed(output.read_text(encoding="utf-8"))
        if current.packaging == "standalone":
            raise ValueError(f"packaged lesson has no editable source copy: {output}")
        shutil.copy2(output, source)

    packaged = package_html(source.read_text(encoding="utf-8"), source, workspace)
    temporary = output.with_suffix(".html.tmp")
    temporary.write_text(packaged, encoding="utf-8")
    temporary.replace(output)
    return source, output


def package_lesson(workspace: Path, lesson_id: str) -> tuple[Path, Path]:
    workspace = workspace.expanduser().resolve()
    return package_page(workspace, workspace / "lessons" / f"{lesson_id}.html")


def lesson_ids(workspace: Path, selected: list[str]) -> list[str]:
    if selected:
        return sorted(set(selected))
    manifests = sorted((workspace / "assets" / "manim").glob("*/manifest.json"))
    ids: list[str] = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        lesson_id = manifest.get("lesson_id")
        if not isinstance(lesson_id, str) or not lesson_id:
            raise ValueError(f"manifest has no lesson_id: {manifest_path}")
        ids.append(lesson_id)
    if not ids:
        raise ValueError(f"no Lumanim manifests found under {workspace}")
    return sorted(set(ids))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--lesson", action="append", default=[], help="package only this lesson id")
    parser.add_argument("--no-index", action="store_true", help="do not package workspace/index.html")
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    for lesson_id in lesson_ids(workspace, args.lesson):
        source, output = package_lesson(workspace, lesson_id)
        print(
            f"PACKAGED: {lesson_id} from {source.relative_to(workspace)} "
            f"to {output.relative_to(workspace)} ({output.stat().st_size:,} bytes)"
        )
    index = workspace / "index.html"
    if not args.no_index and index.is_file():
        source, output = package_page(workspace, index)
        print(
            f"PACKAGED: index from {source.relative_to(workspace)} "
            f"to {output.relative_to(workspace)} ({output.stat().st_size:,} bytes)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

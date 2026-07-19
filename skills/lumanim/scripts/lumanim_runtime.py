#!/usr/bin/env python3
"""Serve a trusted Lumanim lesson and stream one selected resident ManimGL visual."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import importlib.util
import io
import json
import os
import queue
import re
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HOST = "127.0.0.1"
MAX_BODY = 64 * 1024
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass
class RenderRequest:
    state: dict[str, Any]
    done: threading.Event = field(default_factory=threading.Event)
    frame: bytes | None = None
    error: Exception | None = None


def resolve_live_visual(
    workspace: Path,
    lesson_id: str,
    visual_id: str | None = None,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Resolve one live-capable visual without importing its executable scene."""
    lesson_bundle = workspace / "assets" / "manim" / lesson_id
    manifest = json.loads((lesson_bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("lesson_id") != lesson_id:
        raise ValueError("lesson_id does not match the requested lesson.")

    if manifest.get("schema_version") == 1:
        if visual_id is not None and visual_id != lesson_id:
            raise ValueError(f"Unknown visual {visual_id!r} for lesson {lesson_id!r}.")
        selected = dict(manifest)
        selected["visual_id"] = lesson_id
        selected["bundle"] = "."
    elif manifest.get("schema_version") == 2:
        visuals = manifest.get("visuals")
        if not isinstance(visuals, list) or not visuals:
            raise ValueError("Schema 2 lesson has no visual bundles.")
        if visual_id is None:
            live_visuals = [
                visual
                for visual in visuals
                if isinstance(visual, dict)
                and isinstance(visual.get("live"), dict)
                and visual["live"].get("enabled")
            ]
            if not live_visuals:
                raise ValueError("This lesson has no live-capable visual.")
            if len(live_visuals) > 1:
                raise ValueError("This lesson has multiple live visuals; select one with --visual.")
            selected = dict(live_visuals[0])
        else:
            selected = next(
                (
                    dict(visual)
                    for visual in visuals
                    if isinstance(visual, dict) and visual.get("visual_id") == visual_id
                ),
                None,
            )
            if selected is None:
                raise ValueError(f"Unknown visual {visual_id!r} for lesson {lesson_id!r}.")
    else:
        raise ValueError("Unsupported or missing manifest schema_version.")

    selected_id = selected.get("visual_id")
    if not isinstance(selected_id, str) or not SLUG.fullmatch(selected_id):
        raise ValueError("Selected visual has an invalid visual_id.")
    live = selected.get("live")
    if not isinstance(live, dict) or not live.get("enabled"):
        raise ValueError(f"Visual {selected_id!r} does not declare live mode.")
    relative = selected.get("bundle")
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Selected visual bundle must be a relative path.")
    bundle = (lesson_bundle / relative).resolve()
    try:
        bundle.relative_to(lesson_bundle.resolve())
    except ValueError as error:
        raise ValueError("Selected visual bundle escapes the lesson bundle.") from error
    if not (bundle / "scene.py").is_file():
        raise ValueError("Selected visual has no scene.py.")
    return bundle, manifest, selected


class LiveRenderer:
    def __init__(self, workspace: Path, lesson_id: str, visual_id: str | None = None):
        self.workspace = workspace
        self.bundle, self.manifest, self.visual = resolve_live_visual(
            workspace, lesson_id, visual_id
        )
        live = self.visual["live"]
        if not live.get("enabled"):
            raise ValueError("This visual does not declare live mode.")
        class_name = self.visual.get("live_scene_class")
        if not class_name:
            raise ValueError("live_scene_class is missing from manifest.json")

        os.chdir(self.bundle)
        sys.path.insert(0, str(self.bundle))
        module_name = f"lumanim_{lesson_id}_{self.visual['visual_id']}".replace("-", "_")
        spec = importlib.util.spec_from_file_location(module_name, self.bundle / "scene.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load scene.py")
        module = importlib.util.module_from_spec(spec)
        # ManimGL initializes its own CLI configuration during import. Keep
        # companion arguments out of that parser, then restore them.
        original_argv = sys.argv[:]
        try:
            sys.argv = [str(self.bundle / "scene.py")]
            spec.loader.exec_module(module)
        finally:
            sys.argv = original_argv
        scene_class = getattr(module, class_name)

        resolution = tuple(live.get("resolution", [960, 540]))
        fps = int(live.get("fps", 30))
        self.scene = scene_class(
            camera_config={"resolution": resolution, "fps": fps},
            skip_animations=True,
        )
        self.scene.build_lumanim()
        self.lock = threading.Lock()
        self.frames = 0
        self.started = time.monotonic()

    def render(self, state: dict[str, Any]) -> bytes:
        with self.lock:
            self.scene.set_lumanim_state(state)
            self.scene.update_frame(0, force_draw=True)
            image = self.scene.get_image().convert("RGB")
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=False)
            self.frames += 1
            return output.getvalue()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": "3b1b/manim",
            "commit": self.manifest["manimgl"]["commit"],
            "lesson_id": self.manifest["lesson_id"],
            "visual_id": self.visual["visual_id"],
            "frames": self.frames,
            "uptime_seconds": round(time.monotonic() - self.started, 3),
        }


def make_handler(
    workspace: Path,
    renderer: LiveRenderer,
    render_queue: queue.Queue[RenderRequest],
    port: int,
):
    allowed_origins = {f"http://{HOST}:{port}", f"http://localhost:{port}"}

    class Handler(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(workspace), **kwargs)

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _origin_allowed(self) -> bool:
            origin = self.headers.get("Origin")
            return origin is None or origin in allowed_origins

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/api/status":
                if not self._origin_allowed():
                    self._json({"ok": False, "error": "origin rejected"}, HTTPStatus.FORBIDDEN)
                    return
                self._json(renderer.status())
                return
            super().do_GET()

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/frame":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not self._origin_allowed():
                self._json({"ok": False, "error": "origin rejected"}, HTTPStatus.FORBIDDEN)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_BODY:
                self._json({"ok": False, "error": "invalid request size"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                state = json.loads(self.rfile.read(length))
                if not isinstance(state, dict):
                    raise ValueError("state must be an object")
            except (ValueError, TypeError, KeyError) as error:
                self._json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            request = RenderRequest(state)
            render_queue.put(request)
            if not request.done.wait(timeout=10):
                self._json({"ok": False, "error": "render timed out"}, HTTPStatus.GATEWAY_TIMEOUT)
                return
            if request.error is not None or request.frame is None:
                self._json(
                    {"ok": False, "error": f"render failed: {request.error}"},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            frame = request.frame
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(frame)

        def log_message(self, format: str, *args) -> None:
            print(f"[{self.log_date_time_string()}] {format % args}")

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--lesson", required=True, help="Lesson id from manifest.json")
    parser.add_argument(
        "--visual",
        help="Visual id; optional when the lesson has exactly one live-capable visual",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--trust-scene",
        action="store_true",
        help="Required acknowledgement that scene.py is trusted executable Python",
    )
    args = parser.parse_args()
    if not args.trust_scene:
        raise SystemExit("Refusing to execute scene.py without --trust-scene")
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Port must be between 1024 and 65535")
    if not SLUG.fullmatch(args.lesson):
        raise SystemExit("Lesson id must contain only lowercase letters, digits, and hyphens")
    if args.visual is not None and not SLUG.fullmatch(args.visual):
        raise SystemExit("Visual id must contain only lowercase letters, digits, and hyphens")

    workspace = args.workspace.expanduser().resolve()
    renderer = LiveRenderer(workspace, args.lesson, args.visual)
    render_queue: queue.Queue[RenderRequest] = queue.Queue()
    server = ThreadingHTTPServer(
        (HOST, args.port),
        make_handler(workspace, renderer, render_queue, args.port),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    lesson = f"http://{HOST}:{args.port}/lessons/{args.lesson}.html"
    print(f"Lumanim live: {lesson}")
    print("Loopback only. Press Ctrl-C to stop.")
    server_thread.start()
    try:
        while server_thread.is_alive():
            try:
                request = render_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                # OpenGL remains on the main thread that created the context.
                request.frame = renderer.render(request.state)
            except Exception as error:
                request.error = error
            finally:
                request.done.set()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

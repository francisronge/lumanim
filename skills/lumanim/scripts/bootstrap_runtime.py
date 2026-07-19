#!/usr/bin/env python3
"""Create Lumanim's isolated, pinned ManimGL runtime."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MANIM_REPOSITORY = "https://github.com/3b1b/manim.git"
MANIM_COMMIT = "6199a00d4c1b1127ebe45cb629c3f22538b10e13"
EXTRA_REQUIREMENTS = ("trimesh==4.12.2", "PyWavefront==1.3.3")
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 13)


def default_runtime_dir() -> Path:
    override = os.environ.get("LUMANIM_RUNTIME_DIR")
    if override:
        return Path(override).expanduser()
    suffix = MANIM_COMMIT[:12]
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Lumanim"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Lumanim"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "lumanim"
    return base / "runtimes" / suffix


def inspect_python(executable: str | Path) -> tuple[int, int, int]:
    try:
        result = subprocess.run(
            [str(executable), "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            check=True,
            capture_output=True,
            text=True,
        )
        version = tuple(int(part) for part in result.stdout.strip().split("."))
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        raise SystemExit(f"Could not inspect Python executable {executable}: {error}") from error
    if len(version) != 3:
        raise SystemExit(f"Could not parse Python version from {executable}")
    if not MIN_PYTHON <= version[:2] <= MAX_PYTHON:
        shown = ".".join(str(part) for part in version)
        raise SystemExit(f"Lumanim needs Python 3.10-3.13; {executable} is Python {shown}.")
    return version


def find_python(explicit: str | None) -> str:
    if explicit:
        candidate = shutil.which(explicit) or explicit
        path = Path(candidate)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise SystemExit(f"Python executable not found: {explicit}")
        inspect_python(candidate)
        return candidate
    for name in ("python3.13", "python3.12", "python3.11", "python3.10"):
        candidate = shutil.which(name)
        if candidate:
            try:
                inspect_python(candidate)
            except SystemExit:
                continue
            else:
                return candidate
    raise SystemExit("Lumanim needs Python 3.10–3.13; none was found.")


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True, **kwargs)


def runtime_python(runtime_dir: Path) -> Path:
    if os.name == "nt":
        return runtime_dir / ".venv" / "Scripts" / "python.exe"
    return runtime_dir / ".venv" / "bin" / "python"


def preflight(python: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="lumanim-preflight-") as temp:
        temp_dir = Path(temp)
        (temp_dir / "custom_config.yml").write_text(
            "directories:\n"
            f"  base: {json.dumps(str(temp_dir))}\n"
            f"  cache: {json.dumps(str(temp_dir / 'cache' / 'manim'))}\n"
            "camera:\n"
            "  resolution: \"(320, 180)\"\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["MPLCONFIGDIR"] = str(temp_dir / "cache" / "matplotlib")
        code = (
            "from manimlib import Camera; "
            "camera=Camera(resolution=(320,180)); "
            "print('ManimGL OpenGL:', type(camera.ctx).__name__, camera.get_pixel_shape())"
        )
        run([str(python), "-c", code], cwd=temp_dir, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    parser.add_argument("--python", help="Python 3.10–3.13 executable")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()

    runtime_dir = args.runtime_dir.expanduser().resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    python = runtime_python(runtime_dir)
    if not python.exists():
        run([find_python(args.python), "-m", "venv", str(runtime_dir / ".venv")])
    version = inspect_python(python)

    requirement = f"git+{MANIM_REPOSITORY}@{MANIM_COMMIT}"
    run([str(python), "-m", "pip", "install", requirement, *EXTRA_REQUIREMENTS])

    metadata = {
        "schema_version": 1,
        "engine": "3b1b/manim",
        "repository": MANIM_REPOSITORY,
        "commit": MANIM_COMMIT,
        "python": ".".join(str(part) for part in version),
        "executable": str(python),
    }
    (runtime_dir / "runtime.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if not args.skip_preflight:
        preflight(python)
    print(f"Lumanim runtime ready: {runtime_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

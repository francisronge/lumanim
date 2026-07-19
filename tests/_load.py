from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "lumanim"
EXAMPLE = ROOT / "examples" / "paradoxes"


def load_script(name: str):
    path = SKILL / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"lumanim_test_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

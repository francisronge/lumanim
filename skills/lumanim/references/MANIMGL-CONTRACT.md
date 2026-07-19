# ManimGL contract

## Canonical engine

Lumanim uses Grant Sanderson's `3b1b/manim` implementation, distributed as `manimgl` and imported with:

```python
from manimlib import *
```

The initial compatibility pin is commit `6199a00d4c1b1127ebe45cb629c3f22538b10e13` from `https://github.com/3b1b/manim`. A lesson manifest must name the exact commit used. Changing the pin is a tested compatibility migration, not a casual dependency bump.

Manim Community Edition is not the canonical engine. A browser drawing API, an SVG animation, or a visual imitation is not ManimGL.

## Scene requirements

Each lesson bundle must contain a readable `scene.py` whose explanatory visual is composed and rendered by real ManimGL mobjects, animations, cameras, shaders, or update mechanisms.

Require all of the following:

1. Deterministic output: set the scene seed and record parameter defaults.
2. Explicit typography: record the font family and bundle redistributable fonts when exact reproduction requires them.
3. Reproducible media: record resolution, frame rate, transparency, quality flags, engine commit, and render command.
4. Portable asset paths: resolve files relative to the bundle, never an author's home directory.
5. One visual thesis: every movement or transformation should serve the learning objective.

Avoid TeX when ordinary ManimGL `Text` is sufficient. TeX remains available when notation requires it, but the runtime preflight must then verify a LaTeX installation.

## Meaningful-use test

Ask: “If I remove this scene and leave the prose, controls, and quiz intact, does the lesson lose a relationship the learner needed to see?”

- **Yes:** ManimGL is doing explanatory work.
- **No:** the scene is decoration; redesign it before rendering.

## Authoring versus learning

ManimGL's native window, `embed()`, and `interact()` are excellent authoring tools. They are not Lumanim's learner interface. Learner interaction travels through the HTML companion protocol in `RUNTIME.md`; the exact ManimGL render remains embedded as fallback.

# Lumanim

Lumanim is an Agent Skill that keeps Matt Pocock's complete `/teach` method and adds real [3b1b ManimGL](https://github.com/3b1b/manim) visual explanations.

The learner receives one HTML lesson containing as many authored ManimGL explanations as the learning objective requires. Each remains useful offline and can optionally transition into live exploration backed by the same real ManimGL scene.

## What Lumanim preserves

- `/teach` remains the teaching method: mission, trusted sources, proximal difficulty, retrieval, feedback, references, and learning records.
- ManimGL remains ManimGL: editable `scene.py`, a pinned `3b1b/manim` commit, render metadata, inspection evidence, and exact fallback media.
- HTML remains the learner-facing surface. Python and native ManimGL windows are authoring or optional local-runtime concerns.
- Visual design belongs to each teaching workspace. Lumanim ships behavior, not a house stylesheet or imitation renderer.

## Install

With the Skills CLI:

```bash
npx skills add francisronge/lumanim
```

Or copy [`skills/lumanim`](skills/lumanim) into the skills directory used by an Agent Skills-compatible client. The canonical folder follows the [Agent Skills format](https://agentskills.io/).

Invoke `/lumanim` and name what you want to learn. Lumanim is intentionally user-invoked. The repository includes both Claude-compatible invocation metadata and Codex metadata.

## Runtime requirements

Rendered lessons need only a browser. Creating lessons or enabling live exploration requires:

- Python 3.10-3.13
- Git
- FFmpeg and FFprobe
- an OpenGL-capable environment

The bootstrap creates an isolated runtime and installs the pinned ManimGL commit:

```bash
python skills/lumanim/scripts/bootstrap_runtime.py
```

Run a trusted live-capable lesson with:

```bash
<runtime-python> skills/lumanim/scripts/lumanim_runtime.py \
  --workspace <teaching-workspace> \
  --lesson <lesson-id> \
  --visual <visual-id> \
  --trust-scene
```

`--visual` is optional when the lesson has only one live-capable ManimGL bundle.

`scene.py` is executable Python. Read [SECURITY.md](SECURITY.md) before running a scene obtained from someone else.

## Platform status

| Capability | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Rendered HTML fallback | Verified | Portable by design, unverified | Portable by design, unverified |
| Runtime bootstrap | Verified | Implemented, unverified | Implemented, unverified |
| Live ManimGL exploration | Verified | Unverified | Unverified |

An unverified or unavailable runtime never invalidates a lesson: the exact rendered fallback remains the lesson's baseline.

## Examples

[Open the Ship of Theseus lesson](https://francisronge.github.io/lumanim/lessons/0001-ship-of-theseus.html)

[Open the Sorites lesson](https://francisronge.github.io/lumanim/lessons/0002-sorites.html)

[Open the Liar lesson](https://francisronge.github.io/lumanim/lessons/0003-liar.html)

Together, these form a three-lesson Paradoxes course with five real ManimGL visual bundles. [Browse the complete course source](examples/paradoxes), or run a live-capable visual locally with the trusted companion.

*(produced by GPT 5.6 Sol high)*

## Development

```bash
python -m unittest discover -s tests -v
python skills/lumanim/scripts/verify_lesson.py examples/paradoxes
node --check skills/lumanim/assets/lumanim-live.js
node --check skills/lumanim/assets/teach-choice.js
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the acceptance boundary.

## Provenance and license

Lumanim is MIT licensed. The embedded `/teach` contract and ManimGL dependency remain under their upstream MIT licenses; exact pins and notices live in [`skills/lumanim/references`](skills/lumanim/references).

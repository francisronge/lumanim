# Lumanim

Lumanim is an Agent Skill that keeps Matt Pocock's complete `/teach` method and adds real [3b1b ManimGL](https://github.com/3b1b/manim) visual explanations.

The learner receives one HTML lesson. It opens with an authored ManimGL video or image, remains useful offline, and can optionally transition into a live exploration backed by the same real ManimGL scene.

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
  --trust-scene
```

`scene.py` is executable Python. Read [SECURITY.md](SECURITY.md) before running a scene obtained from someone else.

## Platform status

| Capability | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Rendered HTML fallback | Verified | Portable by design, unverified | Portable by design, unverified |
| Runtime bootstrap | Verified | Implemented, unverified | Implemented, unverified |
| Live ManimGL exploration | Verified | Unverified | Unverified |

An unverified or unavailable runtime never invalidates a lesson: the exact rendered fallback remains the lesson's baseline.

## Example

[`examples/ship-of-theseus`](examples/ship-of-theseus) is the first end-to-end proof. Open its lesson directly from disk for the rendered experience, or run the trusted companion to add live plank replacement.

The example uses its own subject-specific stylesheet. It is not a Lumanim theme or template.

## Development

```bash
python -m unittest discover -s tests -v
python skills/lumanim/scripts/verify_lesson.py examples/ship-of-theseus
node --check skills/lumanim/assets/lumanim-live.js
node --check skills/lumanim/assets/teach-choice.js
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the acceptance boundary.

## Provenance and license

Lumanim is MIT licensed. The embedded `/teach` contract and ManimGL dependency remain under their upstream MIT licenses; exact pins and notices live in [`skills/lumanim/references`](skills/lumanim/references).

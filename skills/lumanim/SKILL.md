---
name: lumanim
description: Teach through real ManimGL visual lessons in a stateful HTML learning workspace.
disable-model-invocation: true
license: MIT
---

# Lumanim

Lumanim keeps the complete `/teach` method and adds real ManimGL as a required visual-explanation medium. The HTML lesson is the learner's only interface; ManimGL is the visual engine behind it.

## Non-negotiable inheritance

Before doing anything else, read [the embedded upstream `/teach` contract](./references/teach/TEACH-CONTRACT.md) completely. Follow every instruction in it. Its linked format files live beside it and are part of the inherited contract.

Lumanim only adds requirements. If this file and `/teach` appear to conflict, satisfy both; never weaken `/teach` to make the Manim work easier.

## Workflow

### 1. Re-enter the teaching workspace

Apply `/teach` to inspect or establish `MISSION.md`, `RESOURCES.md`, `learning-records/`, `lessons/`, `reference/`, `assets/`, and `NOTES.md`. Read prior learning state before choosing the next lesson.

**Complete when:** the lesson target is tied to the mission and sits in the user's zone of proximal development.

### 2. Design the understanding, not decoration

Write a one-sentence learning objective and a compact visual storyboard. Use as many ManimGL visual beats as the understanding requires; state what each reveals over time or under learner control and why ManimGL makes that relationship easier to understand.

Reject any proposed ManimGL visual whose removal would leave the explanation equally strong. Read [MANIMGL-CONTRACT.md](./references/MANIMGL-CONTRACT.md) before authoring any scene.

**Complete when:** every proposed visual carries explanatory work and all visuals serve one coherent learning objective.

### 3. Ground the lesson

Research high-trust sources as required by `/teach`; update `RESOURCES.md`; cite claims in the lesson. Never use visual confidence to disguise weak evidence.

**Complete when:** the lesson's factual claims trace to trusted sources and it recommends a primary source.

### 4. Author the real ManimGL scenes

Create the bundle described in [LESSON-BUNDLE.md](./references/LESSON-BUNDLE.md). A lesson may contain one or more independently reproducible visual bundles. Every canonical source must import `manimlib` from 3b1b/manim. Preserve each editable `scene.py`, engine commit, render settings, seed, fonts, assets, and synchronization metadata.

Use live interaction only when it improves learning. If used, implement the live adapter in [RUNTIME.md](./references/RUNTIME.md). Do not call pre-rendered branching or slow rerendering “live.”

The live scene must preserve the visual thesis and decisive annotations of the rendered explanation. Controls should respond continuously unless the concept itself is discrete.

**Complete when:** every preserved source can reproduce its fallback with the pinned real ManimGL engine.

### 5. Render, inspect, and revise

Render a draft. Inspect representative frames from the actual output—not merely the code—and watch the full motion when timing matters. Fix visual hierarchy, occlusion, clipping, legibility, pacing, continuity, and explanatory ambiguity. Repeat until the render passes [QUALITY-GATES.md](./references/QUALITY-GATES.md).

**Complete when:** both source review and visual review pass, with inspection evidence recorded in the bundle manifest.

### 6. Build the lesson HTML

Produce the `/teach` lesson as one coherent HTML experience. Place each ManimGL explanation where it best advances the learning sequence and embed every exact video or image as an unconditional fallback. For live-capable visuals, default to **explanation then exploration**: play the authored video first, then offer an explicit transition into a manipulable version of the same idea. Let the learner return to the video.

Live mode is a progressive enhancement. If it disconnects, restore the video and offer reconnection. Keep the lesson's essential explanation in the page itself so runtime loss cannot strand the learner behind a broken navigation. Do not narrate runtime mechanics or expose persistent mode/status pills in the learner interface; the video, exploration controls, and recovery action should communicate the available state.

Visual design is a per-workspace creative judgment. Apply `/teach`'s beauty, readability, and course-consistency requirements using the strongest design capability available and the mission, subject, and learner as context. The packaged Lumanim assets are behavior-only. Author the visual language inside the teaching workspace, then reuse that workspace's own components for course consistency.

Include the `/teach` feedback loop, citations, related links, primary source, and invitation to ask the agent follow-up questions. Keep native ManimGL windows for authoring/debugging only.

**Complete when:** the HTML works offline without Python and live mode, if offered, never blocks the lesson.

### 7. Verify and hand off

Run `scripts/verify_lesson.py` on the teaching workspace. Open the lesson and test the fallback. If live mode exists, test video → exploration → continuous manipulation → replay; stop the runtime and verify automatic recovery; restart it and verify reconnection.

Only update learning records or the glossary when the learner has demonstrated the understanding, as required by `/teach`.

**Complete when:** all applicable gates pass and the learner needs only the HTML lesson to use the result.

## Hard gates

- **Real engine:** Use 3b1b/manim ManimGL. No reimplementation, imitation, SVG substitute, CSS recreation, or “Manim-inspired” renderer may satisfy the Manim requirement.
- **Meaningful visuals:** Every Lumanim lesson contains one or more real ManimGL explanations. Each visual must weaken the lesson if removed; bundle count follows pedagogy, not a quota.
- **Sole surface:** The learner uses HTML. A native ManimGL window is never the lesson UI.
- **Exact fallbacks:** Every visual bundle embeds rendered ManimGL media and the lesson remains usable without Python, a server, or network access.
- **Editable sources:** Preserve every scene and its reproducibility inputs. Imported scene code is untrusted and must never execute without explicit learner consent.
- **Optional live mode:** Add it when pedagogically valuable, not by quota. “Live” means a continuously responsive control loop.
- **Explanation then exploration:** A live lab deepens the authored ManimGL explanation; it does not replace or hide it on page load.
- **Honest portability:** Label only verified platforms as verified. Degrade to the rendered fallback everywhere else.

## Resources

- [LESSON-BUNDLE.md](./references/LESSON-BUNDLE.md): required paths and manifest
- [MANIMGL-CONTRACT.md](./references/MANIMGL-CONTRACT.md): engine identity and scene rules
- [RUNTIME.md](./references/RUNTIME.md): managed runtime and live adapter
- [QUALITY-GATES.md](./references/QUALITY-GATES.md): acceptance checklist
- [PROVENANCE.md](./references/PROVENANCE.md): upstream sources, pins, and licenses
- `assets/`: behavior-only clients for feedback and optional live interaction; no visual theme
- `scripts/`: runtime bootstrap, companion server, and lesson verifier

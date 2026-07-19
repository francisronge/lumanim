# Quality gates

All required checks must pass before presenting a lesson.

## Teaching

- The lesson follows every instruction in the embedded `/teach` contract.
- The objective is tightly scoped, mission-linked, and appropriate to the learner.
- Claims are cited; one primary source is recommended.
- A feedback loop makes the learner retrieve, predict, decide, or perform—not merely watch.
- The HTML is short, coherent, attractive, accessible, and useful without live mode.

## ManimGL

- `scene.py` imports `manimlib` from the pinned `3b1b/manim` engine.
- The meaningful-use test passes.
- The source, engine commit, seed, render command, resolution, frame rate, fonts, and local assets are preserved.
- A draft was rendered; representative extracted frames were visually inspected; the full motion was watched when timing mattered.
- No important object is clipped, obscured, illegible, misleadingly animated, or present only as decoration.

## Fallback

- The visual design is traceable to this mission, subject, learner, and teaching workspace.
- Existing components from the teaching workspace are reused for within-course consistency as required by `/teach`.
- The HTML opens directly from disk.
- Poster and exact rendered media use relative paths and load successfully.
- Local stylesheet, script, poster, and media references omit URL query strings so `file:` loading resolves real filesystem paths.
- Direct-file mode hides unavailable live controls instead of presenting an inert or unexplained action.
- Teaching content and feedback remain available without the companion runtime.
- The page makes no false claim that Python or ManimGL travels inside the HTML.

## Live mode, when present

- The authored video is the opening explanation; live exploration begins only after an explicit transition and offers a return to the video.
- The control changes a real resident ManimGL scene through the companion runtime.
- Interaction is visually continuous across the control range unless discreteness is itself the lesson; stale input is coalesced.
- The live scene retains the rendered explanation's decisive labels, endpoint, and visual thesis.
- The runtime is loopback-only and requires explicit trust before executing imported Python.
- Stopping the runtime restores the video, disables unavailable controls, and offers reconnection rather than leaving a broken lesson.
- The learner interface does not narrate implementation mechanics or show persistent runtime-status pills.
- The platform label reflects actual verification.

## Evidence

- `manifest.json` passes `scripts/verify_lesson.py`.
- Inspection frames exist and `inspection.reviewed` is true.
- The final fallback render was produced after the last scene-code change.

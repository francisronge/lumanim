# Contributing

Lumanim accepts changes that preserve both inherited systems: the complete `/teach` contract and real `3b1b/manim` ManimGL.

Before proposing a change:

1. Run the unit tests and lesson verifier documented in `README.md`.
2. Render any changed scene with the pinned engine.
3. Inspect representative frames and the complete motion where timing matters.
4. Update source and media hashes in the manifest after the final render.
5. Test the HTML directly from disk and, when live mode changes, test connection, continuous control, runtime loss, and reconnection.

The skill package contains behavior-only browser assets. Example workspaces may have their own visual systems; changes must not introduce a mandatory Lumanim stylesheet or a substitute renderer.

Windows and Linux claims require evidence from those platforms. Until then, retain the honest unverified labels.

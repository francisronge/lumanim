# Companion runtime

The companion runtime is an optional local bridge between lesson HTML and real ManimGL. It is part of Lumanim, not a separate learner product.

## Managed environment

Run `scripts/bootstrap_runtime.py`. It creates an isolated virtual environment under the selected Lumanim data directory and installs the pinned `3b1b/manim` commit. It must never install into global Python or mutate another project's environment.

Start one explicitly trusted lesson with the runtime Python:

```bash
<runtime>/.venv/bin/python <lumanim-skill>/scripts/lumanim_runtime.py \
  --workspace <teaching-workspace> \
  --lesson <lesson-id> \
  --trust-scene
```

On Windows, use `<runtime>\.venv\Scripts\python.exe`. The server prints the learner URL after ManimGL initializes.

Preflight and report separately:

- Python compatibility
- FFmpeg availability
- OpenGL context creation
- font availability
- LaTeX availability when the scene uses TeX

Failure is non-fatal for the lesson because rendered media is mandatory.

## Trust boundary

`scene.py` is executable Python. The companion must not discover and run arbitrary lesson scenes automatically. The learner chooses a workspace and explicitly trusts the scene bundle before first execution. Bind only to loopback; reject path traversal and cross-origin requests; never expose the runtime to the LAN by default.

## Live scene adapter

A live-capable `scene.py` exports a class named by `manifest.json`. It must provide:

```python
class ShipOfTheseusLive(Scene):
    def build_lumanim(self):
        """Create and add the stable scene graph once."""

    def set_lumanim_state(self, state: dict):
        """Apply validated learner state without rebuilding the process."""
```

The runtime instantiates the real ManimGL scene once, calls `build_lumanim()`, applies each state update, asks ManimGL to update and draw the frame, then returns the framebuffer image to the HTML.

## Responsiveness

For continuous controls such as sliders, keep one scene process alive and coalesce superseded input. The interface should react throughout the gesture; it must not launch a fresh CLI render per pointer event.

Label the mode accurately:

- **Live:** continuously responsive updates from a resident ManimGL scene.
- **Generated:** a discrete request that may take noticeable time.
- **Rendered:** the embedded exact fallback.

If live startup or rendering fails, preserve the current control state where practical, return immediately to rendered mode, disable unavailable controls, and expose a reconnect action.

The page must treat the companion as transient. Check availability without replacing the opening video, retry on an explicit learner action, and expose a reconnect action after a dropped request. A directly opened `file:` lesson disables live controls clearly instead of presenting an inert slider.

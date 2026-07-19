# Lesson bundle

For lesson `0001-ship-of-theseus`, create:

```text
lessons/
  0001-ship-of-theseus.html
assets/
  course.css  # authored for this teaching workspace, not supplied by Lumanim
  lumanim-live.js
  manim/
    0001-ship-of-theseus/
      scene.py
      manifest.json
      poster.png
      fallback.mp4
      inspection/
        frame-*.png
```

Add local fonts, images, audio, and data beside `scene.py` when needed. All HTML paths must be relative so the workspace can be moved or emailed intact. Do not append cache-busting query strings to local asset paths: direct `file:` loading must resolve actual filesystem names.

## Manifest

`manifest.json` is machine-readable evidence, not marketing. Include:

```json
{
  "schema_version": 1,
  "lesson_id": "0001-ship-of-theseus",
  "references": ["reference/identity-claims.html"],
  "scene_class": "ShipOfTheseusLesson",
  "live_scene_class": "ShipOfTheseusLive",
  "manimgl": {
    "repository": "https://github.com/3b1b/manim",
    "commit": "6199a00d4c1b1127ebe45cb629c3f22538b10e13"
  },
  "render": {
    "command": "...",
    "resolution": [1920, 1080],
    "fps": 30,
    "seed": 0,
    "scene_sha256": "...",
    "fallback_sha256": "...",
    "poster_sha256": "..."
  },
  "live": {
    "enabled": true,
    "parameter": "replacement_fraction",
    "range": [0, 1]
  },
  "inspection": {
    "frames": ["inspection/frame-000.png"],
    "reviewed": true,
    "notes": "..."
  }
}
```

Omit `live_scene_class` and set `live.enabled` to `false` when live interaction would not improve learning. List every lesson-specific reference document in `references`. The verifier checks the source, fallback, and poster hashes, so record them only after the final render. Never omit the fallback media.

## HTML contract

The HTML file is the sole learner-facing surface and must:

- link the teaching workspace's own shared stylesheet as required by `/teach`;
- display `poster.png`, then offer the authored `fallback.mp4` explanation first;
- encode the fallback with a browser-supported MP4 profile and place its metadata before media data (`faststart`);
- transition into live exploration only after an explicit learner action;
- let the learner replay the authored explanation after exploring;
- expose the `/teach` feedback loop independently of live mode;
- load `lumanim-live.js` only as a progressive enhancement;
- identify live availability truthfully;
- keep the decisive explanation and identity claims in the lesson page; reference documents are additive review aids;
- restore the video and offer reconnection if the companion disappears;
- retain all learning content if JavaScript is disabled;
- link the primary source, related lessons, and reference documents.

The browser must not execute `scene.py`. Only the trusted local companion may do that, after explicit consent.

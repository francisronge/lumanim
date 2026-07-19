# Lesson bundle

For a lesson with two ManimGL explanations, create one lesson manifest with two visual bundles:

```text
lessons/
  0001-ship-of-theseus.html
assets/
  course.css  # authored for this teaching workspace, not supplied by Lumanim
  lumanim-live.js
  manim/
    0001-ship-of-theseus/
      manifest.json
      visuals/
        gradual-replacement/
          scene.py
          poster.png
          fallback.mp4
          inspection/
            frame-*.png
        rival-reassembly/
          scene.py
          poster.png
          fallback.mp4
          inspection/
            frame-*.png
```

Add local fonts, images, audio, and data beside the `scene.py` that uses them. All HTML paths must be relative so the workspace can be moved or emailed intact. Do not append cache-busting query strings to local asset paths: direct `file:` loading must resolve actual filesystem names.

## Manifest

`manifest.json` is machine-readable evidence, not marketing. Include:

```json
{
  "schema_version": 2,
  "lesson_id": "0001-ship-of-theseus",
  "references": ["reference/identity-claims.html"],
  "manimgl": {
    "repository": "https://github.com/3b1b/manim",
    "commit": "6199a00d4c1b1127ebe45cb629c3f22538b10e13"
  },
  "visuals": [
    {
      "visual_id": "gradual-replacement",
      "bundle": "visuals/gradual-replacement",
      "scene_class": "GradualReplacementLesson",
      "live_scene_class": "GradualReplacementLive",
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
    },
    {
      "visual_id": "rival-reassembly",
      "bundle": "visuals/rival-reassembly",
      "scene_class": "RivalReassemblyLesson",
      "render": {
        "command": "...",
        "resolution": [1920, 1080],
        "fps": 30,
        "seed": 0,
        "scene_sha256": "...",
        "fallback_sha256": "...",
        "poster_sha256": "..."
      },
      "live": { "enabled": false },
      "inspection": {
        "frames": ["inspection/frame-000.png"],
        "reviewed": true,
        "notes": "..."
      }
    }
  ]
}
```

`visual_id` identifies one explanatory unit inside the lesson; `bundle` is its path relative to the lesson manifest. Visual IDs and bundle paths must be unique. Add as many entries as the learning sequence requires, not one by default and not several by quota.

Omit a visual's `live_scene_class` and set `live.enabled` to `false` when live interaction would not improve learning. List every lesson-specific reference document once at lesson level. The verifier checks every source, fallback, poster, and inspection record, so record hashes only after the final render. Never omit a visual's fallback media.

Schema 1 single-visual bundles remain valid for portability. New lessons should use schema 2 even when they begin with one visual, so another can be added without changing the lesson's identity.

## HTML contract

The HTML file is the sole learner-facing surface and must:

- link the teaching workspace's own shared stylesheet as required by `/teach`;
- display every visual's `poster.png`, then offer its authored `fallback.mp4` explanation first;
- encode the fallback with a browser-supported MP4 profile and place its metadata before media data (`faststart`);
- transition any live-capable visual into exploration only after an explicit learner action;
- let the learner replay that visual's authored explanation after exploring;
- expose the `/teach` feedback loop independently of live mode;
- wrap each live-capable visual and its controls in `data-lumanim-experience="<visual-id>"`, matching the manifest;
- load `lumanim-live.js` once as a progressive enhancement;
- identify live availability truthfully;
- keep the decisive explanation and identity claims in the lesson page; reference documents are additive review aids;
- restore the video and offer reconnection if the companion disappears;
- retain all learning content if JavaScript is disabled;
- link the primary source, related lessons, and reference documents.

The browser must not execute `scene.py`. Only the trusted local companion may do that, after explicit consent.

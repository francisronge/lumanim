# Provenance

## `/teach`

- Source: `https://github.com/mattpocock/skills/tree/main/skills/productivity/teach`
- Repository commit used for verification: `9603c1cc8118d08bc1b3bf34cf714f62178dea3b`
- Embedded file: `references/teach/TEACH-CONTRACT.md`
- Embedded `SKILL.md` SHA-256: `6d2dbe5e03084cf26fef66b535127b36cd1bcbe9478e26b0626029cd51dc2259`
- License: MIT, copyright 2026 Matt Pocock

The embedded contract and its four format files are preserved verbatim. The upstream `SKILL.md` was renamed `TEACH-CONTRACT.md` so skill scanners do not register a duplicate `teach` skill. Lumanim's root `SKILL.md` requires agents to read and obey the entire contract before applying additions.

## ManimGL

- Source: `https://github.com/3b1b/manim`
- Initial compatibility commit: `6199a00d4c1b1127ebe45cb629c3f22538b10e13`
- Package metadata version at that commit: `1.7.2`
- License: MIT, copyright 2020–2023 3Blue1Brown LLC

Lumanim depends on ManimGL but does not rename a reimplementation as Manim. Lesson manifests preserve the exact engine commit used to render them.

Before publishing Lumanim, retain both upstream MIT notices in the public repository and document Lumanim's own license separately.

Exact upstream notices are preserved in `references/licenses/TEACH-MIT.txt` and `references/licenses/MANIMGL-MIT.txt`.

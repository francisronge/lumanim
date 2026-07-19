# Security model

Lumanim lesson scenes are executable Python. A lesson's rendered HTML, poster, and video can be inspected without executing the scene; live mode cannot.

## Trust boundary

- The companion binds to `127.0.0.1` and serves one explicitly selected workspace.
- It refuses to import `scene.py` unless the operator passes `--trust-scene`.
- The frame API rejects foreign browser origins, oversized bodies, malformed JSON, and paths outside the served workspace.
- The browser never executes Python. Losing the companion returns the learner to rendered media.

Before trusting a third-party scene, inspect `scene.py` and every local Python module or asset-processing script it imports. Run it under a normal user account in Lumanim's isolated environment, never with elevated privileges.

Security reports should use GitHub's private vulnerability-reporting channel once the repository is public. Avoid publishing exploitable details in a public issue.

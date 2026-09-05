# Beta testing and release notes

Version: 0.1.0-beta.1. Windows development-host verification, September 5, 2026.

Recorded results: all 22 automated tests passed; desktop widget smoke passed; all four tabs visually inspected; packaged executable opened, initialized temporary state and closed cleanly. Build host: Windows 11, Python 3.14.4, PyInstaller 6.22.2. No live ChatGPT account or clean second machine was tested.

## Automated checks

`python -m unittest discover -s tests -v` runs 22 tests with the optional MCP SDK installed (otherwise the MCP integration test is skipped). Tests cover validation, explicit-interest adaptation, private defaults, persistence, undo/history bounds, pause/revocation, expiry, queue bounds, duplicate/concurrent approvals, launch failure, reset and corrupt/future data. The real SDK subprocess test covers discovery, disabled connection, proposal creation, local acceptance, outcome polling, invalid input and pause. It does not connect to the user's ChatGPT account.

`python tools/gui_smoke.py` exercises real Tk widgets using temporary data: preview, apply, undo, save preferences, suggest, record activity, float/hide, and pause/resume. Optional `--screenshots artifacts/screenshots` uses Pillow to capture only the test application. Screenshot capture is a development tool, not a product feature.

Build with `python tools/build_windows.py` after installing `requirements-build.txt`. Run `python tools/package_smoke.py dist/ProjectAura/ProjectAura.exe` to check a visible packaged window, isolated state initialization and clean shutdown. The ZIP has a SHA-256 file. The executable is unsigned; do not disable security controls to run it. Building from source is available.

## Tester walkthrough

1. Start with temporary data: `python run_aura.py --data C:/path/to/test-aura.sqlite3`.
2. Preview an ocean bob with headphones; the floating avatar retains its saved look until Apply.
3. Apply, restart and verify persistence. Undo to restore the previous look.
4. Save interests. Record an activity with adaptation off; the look stays the same. Enable adaptation, save and record; the theme updates and remains undoable.
5. Enable MCP, send a proposal, then reject it. Repeat and accept. Pausing or disabling the connection must cancel pending requests.
6. Use the Notepad demo and accept to open an empty window. Status reports launch submission; no text is entered. Close Notepad normally.
7. Export preferences, reset Aura and verify interests, history and requests are gone and connection is disabled. Exports remain your responsibility.

## Limits and unverified behavior

- Original procedural 2D artwork; no arbitrary 3D mesh remodeling or LLM fine-tuning.
- Offline keyword parser, not general AI chat. A configured MCP client can supply language reasoning.
- Only Notepad launch is implemented; actual window/task completion is not verified. No CAD, hardware, game input, voice, microphone or screen reading.
- ChatGPT account integration needs supported access; no particular app/account has been certified.
- Tested with Python 3.14 on the Windows development host. Source targets Python 3.11+; other Python/OS versions and clean-machine packaging remain unverified.
- Minimum desktop size 1080 x 780. Small displays, screen readers, multi-monitor changes and extensive DPI combinations need testing.
- Float window is movable and topmost, not fully click-through. No startup registration, tray service, auto-update or installer.
- Plaintext SQLite uses the OS user boundary; other same-user processes may access it. Exports are preference snapshots, not full database backups; no import UI yet.
- Remote requests may wait while desktop is closed but cannot execute without local approval; they expire after ten minutes.
- No claim of exhaustive legal review, penetration testing, supply-chain audit or production readiness.

## Gates before broad distribution

Clean Windows machine, actual ChatGPT tunnel/account, assistive-technology and scaling tests, dependency advisory review, trusted code signing, repeatable build provenance and incident handling. Preserve source and license notices with redistributed packages.

# Project Aura 0.6.0-beta.1

A local Windows beta with an optional 64-second narrated entrance/tutorial and a matching shareable MP4. Aura is the focus: helicopter arrival, a staged breach, landing, body scan, appearance preview, equipment, elemental effects and local voice. It is a stylized 2D performance, not final skeletal animation or a video-generation illusion.

## Working changes

- Visible Controls button on floating Aura; Studio control entry and focused Ctrl+Space. The wheel is raised again after animation redraws, including the classic renderer. Animation scheduling now yields to Tk idle geometry updates so busy surfaces do not prevent tabs/windows from mapping. Shift-hover is retained as an optional shortcut, not the only access path.
- Holster, satchel, charm and spell slots with persistence, removal and undo. Three visual spell styles. Declarative creator item import with validation and attribution; two examples included.
- Same local Scene renderer for the video and the optional in-app tour. Sound starts muted; play/pause, replay, close and Try this feature are available. The tour does not write preview looks to the user's profile.
- Local narrated audio with mouth movement, captions and original synthesized sound effects. No downloaded music or game sound effects.
- Portable AuraMCP.exe and Copy MCP setup. A sixth tool queues approved visual cues; there is no remote approve tool.
- Version shown in the Studio title, updated setup and contributor documentation.

## Test coverage and practical limits

Unit/protocol tests cover state, queue permissions, speech validation, motion, creator import, persistence/undo and scene boundaries. GUI regression scripts cover floating from Appearance, mouth preview, wheel access without Shift, classic-renderer redraw, equipment effects and tutorial pause/close with an isolated profile. Packaged desktop and bridge are separately smoke-tested. These checks are on the development host, not a claim of every Windows setup working.

The grand entrance runs inside a stage window. It does not punch through a real monitor, destroy icons, operate Fusion, or complete CAD work. Props attach visually; reveal/stow is floating, not a rigged hand drawing a blade. Independent apparel pieces, arbitrary custom models and high-detail body actions remain unfinished. ChatGPT's built-in Voice stream is not connected; local speech and selected WAV playback work independently.

## Data and compatibility

Existing preferences remain in the same local SQLite profile. Equipment uses a sibling .equipment.json file; it contains imported item definitions and selected slots, not executable content. Reset removes this equipment data as well as resetting Aura's database. Export includes equipment definitions and slots. Do not run multiple Aura versions against the same profile simultaneously.

No new network listener, microphone capture or telemetry is added. Ordinary tour playback is offline. The MCP bridge runs stdio; requests remain gated by the existing local approval queue. Client/model providers have their own data handling outside Aura.

The Windows ZIP is unsigned. Keep the entire extracted folder. The source bundle excludes user state, local paths, credentials, caches and build output. Funding is not connected and no donations are collected by the app.

## Reproduce media

Install requirements-media.txt and run tools/create_tour_audio.py on Windows to generate the narration without playing it. Then tools/export_demo.py writes a 960×540, 24 fps H.264/AAC MP4, SRT captions, poster and checksum. Frames come from the same scene implementation the beta plays, not separately generated action footage. Windows speech voices and system fonts are used locally; voice engines and font files are not redistributed.

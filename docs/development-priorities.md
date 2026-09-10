# Remaining work, ordered by user impact

**Current embodiment priority:** [Skeleton Zero](skeleton-zero.md), a real rigged
Unreal body driven through a semantic protocol. The list below describes older 2D
beta work; it no longer sets the order for the 3D effort. See the revised
[roadmap](roadmap.md) before selecting new work.

Beta 7 adds an optional illustrated body on the shared 2D rig, alongside persistent model imports, tray recovery, startup-only updates and app/device audio meters. The following remain unfinished.

1. Layered body rig and expressive face: separate jaw, authored intermediate mouth shapes, eyes, brows, hands, forearms, hair clumps and clothing. Add a hand/holster socket contract, occlusion and contact poses. Acceptance: draw and stow a dagger without a floating prop, doubled lips or body seams.
2. Broader interaction reliability: automated physical Windows hit-testing, transparent-window behavior across display scales and multiple monitors, keyboard-only navigation and lower-resolution layouts. The explicit Controls button and Studio route now avoid dependence on hover/modifier settings; focused Ctrl+Space is not a global hotkey.
3. Apparel and model creator packs: versioned rig compatibility, slots, authored images/meshes, safe dimensions/path validation, import preview, undo and missing-asset recovery. The item importer supports procedural variants; Aura Rig 1 now supports named 2D joints and PNG layers, with a persistent local model library and missing-asset recovery. Apparel packs and 3D adapters remain open.
4. Voice expression: visemes/phoneme timing, emotion-specific facial poses and a separately configured streaming voice provider. Built-in GPT Voice output has no implemented feed in this app. Do not intercept credentials, private app internals or unrelated system audio as a shortcut.
5. Preset-specific performance: add arcane and mecha entrances using a common timeline, followed by authored movement for blades/bows. Current runtime has a helicopter stage and fire/ice/lightning effects; no mecha body or complete combat rig.
6. Real applications: grow approved adapters one operation at a time with explicit outcomes, cancellation and test fixtures. Notepad is the current proof of launching. CAD, machine geometry, game co-op and hardware control remain separate projects needing domain fixtures and actual integration tests.
7. Distribution: clean-machine Windows matrix, signed installer/update channel, crash recovery and profiling. The current unsigned portable updater checks official release URLs, SHA-256 hashes, safe extraction and executable preflight, retaining older versions. Publisher signatures and broader recovery tests remain open.
8. Community and funding: contribution templates and item examples are included. The owner has submitted GitHub Sponsors signup for review and supplied the funding destination. Keep availability statements aligned with approval status. Publish reproducible beta/source/video assets with matching checksums and accurately bounded release notes.

New features must preserve local approval boundaries, cancel on Pause where relevant and remain optional. Any demonstration must use the runtime implementation or be conspicuously marked as concept art. Prefer completing and testing one vertical slice over increasing the list of unsupported promises.

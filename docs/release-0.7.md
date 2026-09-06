# 0.7.0-beta.3 — a persistent model library

Imported Aura Rig 1 models now appear in a local library. Select one once and Aura restores it on the next launch, including the floating avatar. Restore default Aura keeps your packs available. Reset clears the selection and retains imported artwork.

Packs are revalidated before loading. Missing or damaged selections recover to default Aura with a visible status message; interrupted settings saves preserve the previous selection. Switching bodies clears the previous body’s active motion.

Official Project Aura releases remain free and open source, without paid editions, subscriptions, microtransactions or paid outfit/power unlocks. Optional support is for project costs. The owner has added the GitHub Sponsors funding file; account review is still pending, so this release does not announce that donations are live.

This update does not add new illustrated-body animations, 3D imports, or phoneme/emotion synchronization with ChatGPT Voice. The included video remains the existing illustrated entrance and tour, not a demonstration of the new rig library.

## Tray presence and shared rigs

Aura starts as a floating companion with a system tray icon. Studio opens when requested. **Controls → Menu** can show/hide Studio or the tray icon; hiding the icon is saved. Relaunch the same profile to recover Studio in the existing instance. New MCP requests reopen the approval page if Studio is hidden. New profiles start with the approved Tactical Ops artwork. Closing Studio hides it; **Menu → Quit** exits. `--studio` is available for development and accessibility testing.

The first [Aura Rig 1 importer](model-standard.md) accepts local PNG layers, named joints and attachment sockets. The included reference mannequin demonstrates idle, inspection, wave, articulated fingers and a hand-to-holster draw. It is not a replacement for Aura's approved illustrated artwork. Model selection is saved across restarts in beta 3. VRM, Live2D, arbitrary 3D imports and interchangeable apparel packs remain unfinished.

Presence adds **experimental selected-app audio-level metering** on Windows. Start sound in the desired app, Refresh, choose its process/output session and Follow app. Stop, Pause, local speech, WAV playback or mouth preview disconnect it. This reads a peak meter, without recording PCM, microphone sound or transcripts. Notifications can also animate the mouth. No phoneme timing or automatic emotion inference is provided. Windows routing and app session availability can prevent connection. A live test verified silence and a nonzero signal from a selected muted test process, without PCM capture. This is not yet verified end-to-end ChatGPT Voice synchronization.

Local Windows speech and selected WAV playback remain available. The optional 0.6 helicopter tour and demo use the existing illustrated performance renderer; they do not demonstrate the new rig or a custom model's entrance.

## Verification and limits

58 unit/protocol tests pass, including permission boundaries, invalid model inputs, contact positions, reduced motion, tray settings and single-instance recovery. The live tray/rig check covers hide/restore/relaunch recovery and rendering. Dependency resolution audit reported no known vulnerabilities on 2026-09-06; this is not a security certification. Clean-machine, display-scale and multi-monitor testing remain open. The Windows portable build is unsigned.

## Local data

Appearance, interests, activity counts, equipment and request records use the existing profile. Model selection is stored in a `.model.json` sidecar and cleared by Reset. Tray visibility is stored in a `.ui.json` sidecar; imported model copies live in the adjacent `.models` folder. Reset clears preferences, equipment and requests, but retains tray visibility and imported artwork, as well as external exports/backups. No audio recording or telemetry is added. App session names are listed only when Refresh is requested; metering begins only with Follow app and is not persisted across restarts.

## Community and funding

Contributions are welcome, especially authored face/body layers, compatible rigs, contact animations and reproducible bug reports. The maintainer has configured `.github/FUNDING.yml` for Alexflu; Sponsors review is reported as pending. Do not treat a repository URL as an active payment account.

Beta 2 expands dependency-notice collection to the actual frozen module inventory, including optional installed libraries, and preserves license subdirectories. Runtime features are unchanged from beta 1.

# Studio and motion refinement — 0.4.0-beta.1

Extract the complete ZIP and close your older Aura before launching this executable. Existing appearance and MCP approval behavior are preserved.

## Visible changes

- Runtime removal of the navy artwork backdrop. The floating avatar is now frameless, with no permanent button bar. Drag her, right-click for controls, or double-click for her entrance. Right-click offers resizing, docking, Pause/resume, and Hide. The Studio's Float button also hides/shows her.
- Time-based breathing, body sway, slight head movement, and gentle attention toward the pointer while it is inside Aura's canvas. Feet stay planted. This does not track the pointer elsewhere or inspect other windows.
- Audio mouth movement eases across five blend levels rather than abruptly swapping one open/closed image. Eye blinks are independent, including during speech. This is still amplitude animation, not phoneme alignment.
- Stable stage graphics and reused image buffers reduce redundant drawing. The scheduler targets roughly 30 frames per second; actual rate depends on system/Tk rendering and number/size of avatars. The local short source-window test observed about 22 fps, not a universal guarantee.
- Studio labels use human-readable outfit names while preserving saved/MCP values. Controls unavailable on the illustrated body are hidden. Classic models retain them.

## Current limits

This remains a deformed 2D sprite, not a full jointed rig. There are no authored walks, weapon actions or casting gestures yet. The backdrop key is tuned to this atlas and may leave fine dark edges or isolated imperfections. It is not a general background-removal tool. Gesture range, face accessories, and independent appearance channels still need separate assets. Power styles are documented in power-styles.md as a future modular system, not presented as finished features.

Reduce motion and Pause stop the new movement. Speech, WAV loading and MCP approvals retain the 0.3 controls. Mood and effect choices remain session-only. The new renderer does not add recording, account access, or network calls.

## Checks

38 tests cover state and approvals, speech/audio handling, independent timing, mouth closure, pause, anchored feet, and preservation of dark clothing while removing the background. Desktop smoke checks cover appearance combinations, labels mapping back to saved values, frameless floating, resizing and docking. Packaged launch uses an isolated profile outside the sandbox because of the known Tcl sandbox limitation.

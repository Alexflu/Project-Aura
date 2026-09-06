# Illustrated body preview — 0.2.0-beta.1

Close the old Aura executable before opening this build. Extract the entire ZIP and run ProjectAura.exe with its _internal folder beside it. Your existing preferences remain in the same local database.

Click **Try approved Aura look**, then **Apply look**. Outfit `tactical` is Tactical Ops; `stealth` is Stealth Striker. Hair `pixie` selects the short layered cut; `long` selects long waves. `bob` currently uses the short illustrated cut. Other outfits retain the classic procedural body.

Palette recolors violet accents across hair and clothing together. Independent hair and clothing colors are planned. The illustrated face, jewelry, and proportions are baked into this first atlas; accessory and silhouette controls are disabled for illustrated outfits. They remain available for the classic body.

Idle sway, blinking and **Preview speaking · no audio** are local sprite animation. The speaking button toggles the demonstration until pressed again; Pause and Reduce motion stop animation. This does not listen to a microphone, play audio, or synchronize with built-in GPT Voice. The floating window currently includes the dark artwork backdrop, not a clean transparent cutout.

The source artwork is aura/assets/aura-atlas-v1.png. Its 4 columns contain short tactical, short stealth, long tactical, long stealth. Facial animation uses measured regions from the additional expression rows, holding the body steady. This is a sprite prototype, not a layered rig; subtle seams may remain.

## MCP

Existing stdio configuration still points to run_aura.py --mcp. Restart that MCP server/client connection to pick up the new `stealth` option. Incoming appearance proposals still require local approval. Do not run the previous 0.1 desktop alongside this build after saving stealth: that older binary cannot validate the new outfit value. If you need to return to 0.1, first save an older outfit such as explorer using 0.2.

## Next animation work

Create separately rigged eyes, eyebrows, mouth shapes, hair, accessories, and clothing layers; add independent palette channels and face options; provide a hologram rendering mode. Build audio-driven mouth timing through an explicit supported audio integration, then gestures and entrance sequences. No claim is made that the present sprite demo supplies these features.

## Validation

Core/approval tests and the real stdio SDK round trip cover the new outfit. tools/illustrated_smoke.py exercises all four illustrated combinations, speaking/idle, floating mode, pause, and reduced motion with temporary data and own-window screenshots.

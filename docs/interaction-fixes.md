# Interaction and mouth fixes — 0.5.0-beta.1

Close the older Aura and extract the entire new ZIP before launching.

## Changes

- Floating startup now explicitly maps, raises and refreshes the avatar surface. Tested directly from Appearance without visiting Presence.
- Preview mouth movement now labels itself Stop mouth preview, drives both Studio and floating surfaces, and ends after four seconds. Preview stops local audio first. Pause/Reduce motion still prevent motion.
- Mouth transitions switch between the authored closed and open drawings, preserving the face shading instead of overlapping the lips or stretching the jaw. It is still a low-resolution illustrated approximation, not final facial artwork or phoneme animation.
- Very small secondary deformation along outer hair and clothing adds movement while retaining the face center and feet. It cannot draw items from a bag or holster; that needs separate rigged assets.
- Hold Shift with the pointer over the floating avatar to show a radial control wheel. Keep Shift held while clicking Look, Voice, Preview, Hide, Pause, or Dock. Release Shift to dismiss. Right-click remains available. The app checks only Shift's pressed state and pointer position, without collecting typed text.

Look and Voice open the relevant Studio tab; they do not yet open an inventory. See creator-inventory.md for the planned equipment/spellbook system and creator pack direction. This release adds no asset importer or new task permissions.

## Verification

The interaction smoke test opens Aura from Appearance on a fresh temporary profile, checks the floating surface, samples nonzero mouth movement on both avatars, checks labels and stopping, exercises wheel show/hide, and reopens the avatar. Existing state, voice, rendering and approval tests remain in place. Packaged launch is separately checked outside the sandbox.

The current atlas uses authored closed/open mouth shapes. Intermediate lip shapes need additional artwork; amplitude controls when the mouth opens, rather than stretching the jaw.

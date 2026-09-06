# Aura power styles — design direction

Status: planned. These are visual/performance profiles, not new computer permissions, and are not implemented as powers in the 0.4 build.

## Separate identity, look, and performance

An identity profile selects face, body proportions, voice preference, and signature details. A look selects hair, palette, clothing, armor, and accessories. A power style selects movement vocabulary, props, effects, and task choreography. A loadout selects elements or equipment within a style. Users can lock any category and allow suggestions in the others. A preference or recorded hobby can inform a suggestion; it should not silently replace the user's chosen identity.

Initial creation can start from a power style to suggest an appropriate silhouette/outfit, but styles must remain swappable. An arsenal user can keep a casual outfit; an armored mecha Aura can cast ice. Pure-element and mixed-element casters should both be possible. Mixing styles needs deliberate defaults so every available effect does not fire at once.

## Candidate families

| Family | Direction | Loadouts | Movement language |
| --- | --- | --- | --- |
| Arsenal | Original mischievous punk/tech styling | Pistols, oversized fictional gadgets, launchers | Weight shifts, recoil, smoke, shell effects, theatrical explosions |
| Arcane | Mage or modern spellcaster | Fire, ice, lightning, wind, light, shadow; single or mixed | Hand signs, casting arcs, elemental trails, floating props |
| Blademaster | Agile or composed martial styling | Swords, spears, bows, knives, daggers | Authored ready stances, draws, flourishes, recovery poses |
| Mecha | Armored companion or mechanical styling | Thrusters, deployable tools, shields | Mechanical articulation, HUDs, controlled landings |

References can inform energy and aesthetic; Aura's identity and production assets remain original. The user's existing Tactical Ops and Stealth Striker options remain useful across families.

## Task choreography

The executor emits semantic events: task requested, approved, started, waiting, completed, failed, cancelled. The performance layer chooses an animation for the active family. Example: opening an approved app might use a gadget flourish, a casting gesture, or a blade flourish. A spectacular effect does not execute the task and must not imply success before the executor reports success. Cancel and reduced motion have short static fallbacks. Never animate a fake approval or use explosions as a substitute for an actual error message.

Effects should operate inside Aura's own transparent surface. Interaction targets may eventually use explicitly available app/window geometry, without requiring screenshots or unrelated desktop content. No destructive modifications to icons/files, hidden clicks, or unapproved actions are needed to sell the illusion.

## Asset and rig work required first

The current sprite is a starting illustration, not a skeleton rig. Before convincing powers: separate head/eyes/brows/mouth/hair, torso, upper/lower arms, hands, hips/legs, outfit overlays, and props; author pivots, occlusion and neutral poses. Then make a small reusable set of idle, attention, nod, reach, anticipation, action, recovery, and cancel motions. Effects follow motion timing rather than covering up missing movement.

Style packs should eventually be versioned data referencing local assets and named animation clips, with no executable scripts. Validate dimensions, sizes, clip duration and supported event names. Missing assets fall back to the neutral style. Model-changing proposals stay previewable and reversible. The helicopter entrance belongs after this foundation, not before it.

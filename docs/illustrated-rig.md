# Illustrated Aura body rig

In Models, choose **Try illustrated Aura rig**. Wave, Bow, Draw and casting use
the same named-joint implementation as the technical reference and creator packs.
Casting and drawing require the corresponding equipped item. Default Aura restores
the previous sprite; imported art and preferences are retained.

The new body deliberately remains optional: facial expressions, lip timing,
independent finger layers, soft skin-joint deformation and collision-aware cloth
are unfinished. Existing accessories drawn into the shorts are part of that art,
not removable inventory. Its separate back-hair layer has shared secondary motion.

`aura/assets/aura-rig-sheet-v1.png` is the original generated source, including its
provenance metadata. It was produced with the built-in image-generation tool using
the previously approved Project Aura direction as a reference. The tool returned
RGB checkerboard imagery instead of true transparency. `tools/build_illustrated_rig.py`
imports the sixteen known cells, removes connected neutral background, trims the
forearm cells, and writes an Aura Rig 1 pack to `aura/assets/aura-illustrated-rig`.
The source is retained unchanged. Generated artwork is distributed under this
project's MIT terms to the extent the project holds applicable rights.

## Generation prompt

Create a production 2D skeletal-animation sprite-part sheet for the adult original
character Aura using the approved reference. Match Stealth Striker: black tactical
crop top, shorts and belts, thigh-high stockings, chunky combat boots with violet
trim, tattooed upper arms, fingerless gloves, violet eyes, and short asymmetrical
black hair with violet ends. Detailed clean anime cyberpunk illustration.
Exactly four columns by four rows, sixteen isolated parts, one per cell, transparent
background, no text, grid lines or background shadows. Front-facing limbs point
down, with generous padding and complete rounded overlap ends. Row one: complete
head with front hair, torso, pelvis/shorts, back hair. Row two: left and right upper
arms, left and right forearms. Row three: left and right relaxed gloved hands,
left and right thighs. Row four: left and right lower legs, left and right boots.
Human adult proportions, no animal ears, preserve the approved identity and palette.

The prompt above records the production specification. The resulting sheet needs
the documented importer corrections; it is not an automatically production-ready rig.

## Reproduce the runtime preview

Run `python tools/export_rig_preview.py aura/assets/aura-illustrated-rig/model.json artifacts/aura-illustrated-motion.gif` and `python tools/export_music_preview.py` before `python tools/create_release_kit.py`.
The GIF and poster use the program renderer with the equipped built-in items.
They are distinct from the existing narrated entrance tutorial.

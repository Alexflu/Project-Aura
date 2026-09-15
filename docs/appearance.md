# Aura appearance

The approved direction is `aura/assets/approved-direction.png`: a stylized face,
violet eyes, black hair with violet ends, tattoos, and black/grey tactical clothing
with violet details. The assembled Ada MetaHuman is a temporary body, not a change
to that direction.

## First material pass

`AuraAppearance.cpp` applies a runtime palette to the assembled character: dark
hair with violet dye, violet iris multiplication, and charcoal/violet clothing
colors. It uses the existing materials' parameters, preserving the facial rig,
groom and clothing textures. It does not save or overwrite Epic assets. The same
palette is used in the stage and desktop host; restart the host after rebuilding.
Launch Unreal with `-AuraOriginalMaterials` to inspect the unmodified preset.

The parameter names were inspected on the locally assembled UE 5.6.1 asset.
Missing parameters emit warnings rather than substituting unrelated materials.
This is color direction only: baked iris texture affects the resulting tint, and
different groom LODs and lighting can change the apparent saturation. The short
coiled preset does not reproduce the illustration's distinct violet hair tips.

## Next asset work, in order

The [fitted wardrobe contract](wardrobe.md) describes importing full outfit parts
and enabling them on the existing animated body. Epic Techwear is now locally
fitted and assembled as a temporary reference. The separate garment loader
preserves the assembled outfit when a supplied replacement is incompatible.

### Working hairstyle: fitted messy bob

The current configured groom is Epic's `Hair_M_BobMessy`, fitted to Aura's existing
face. A local desktop check on 2026-09-15 showed a fuller outline and side-swept
fringe compared with the previous layered groom. It remains an intermediate
hairstyle: the illustrated spikes, violet tip definition and final shading are
not complete. No face geometry or rig was changed.

Prepare this optional local asset once:

```powershell
python tools/unreal_body.py prepare-hair --hair-style Hair_M_BobMessy
```

The provenance report is `Saved/Aura/messy-bob-hair-manifest.json`. Prepared styles
have separate asset and binding paths, so preparing the bob preserves the layered
groom. `[Aura.Appearance]` in `Config/DefaultGame.ini` selects `Groom` and
`GroomBinding`; always change both together. Restart the host to apply a selection.
Missing or incompatible pairs retain the assembled preset. To return to the
previous layered style, set both paths to `Hair_M_Layered` and
`Hair_M_Layered_Binding` under `/Game/Aura/Appearance`, or remove both settings.
`-AuraOriginalHair` bypasses this selection entirely.

### Preserved layered hair

After assembling the face, run `python tools/unreal_body.py prepare-hair` once,
then restart the desktop host after selecting that pair. This copies Epic's installed medium
layered groom and creates a binding from its reference head to Aura's face under
`/Game/Aura/Appearance`. The runtime uses this pair when compatible; missing assets
keep the assembled hair. `-AuraOriginalHair` explicitly selects the preset hair.
The local provenance report is `Saved/Aura/layered-hair-manifest.json`.

When replacing the assembled groom, the runtime clears its old material overrides
before applying the new groom and Aura palette. The locally assembled coiled hair
uses cards/strands/helmet slots, while the layered groom uses strands/cards/helmet.
Keeping overrides by index therefore applies the wrong material to the first two
slots. Each replacement must start from its own groom materials, not the previous
hairstyle's textures or slot order. The original-hair option retains the assembled
materials because it bypasses replacement.

The groom retains references to installed MetaHuman Creator content. Packaging
must migrate those dependencies before distributing a standalone build. The
generated files stay local and are not relicensed or committed as MIT assets.
This improves the silhouette; it does not finish the illustrated spiky cut or
establish final hair physics. Rebind and inspect after changing the face mesh.

1. Replace the short coiled preset hair with the approved layered silhouette and
   violet ends. Keep compatible groom bindings or a properly skinned hair mesh.
2. Build the fitted black tactical outfit, grey outerwear, straps and boots around
   the existing body proportions. Reuse its skeleton and animation library.
3. Refine facial proportions toward the illustration while retaining expression
   controls; then add the tattoo textures and accessories.

Use original or appropriately licensed assets. Record provenance before importing
third-party content. MIT source licensing does not relicense Epic binaries.
Do not treat recoloring the temporary preset as completion of these asset gates.

For appearance-only changes, build if native code changed and inspect the affected
materials in one live session. Repeat broader behavior tests only when animation,
speech, lifecycle or shared interfaces change; no new demo recording is required.

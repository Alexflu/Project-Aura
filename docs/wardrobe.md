# Fitted wardrobe assets

The current local installation contains only MetaHuman's basic shirt and shorts.
No tactical jacket, trousers or boots have been added yet. The runtime now accepts
up to eight fitted skeletal garment parts without changing the animation adapter.

## Selected starting outfit: Epic Techwear

[Epic's MetaHuman Techwear Outfit](https://www.fab.com/listings/9e04c752-1979-4723-b78f-6d24afc532bc)
is a free parametric jacket, pants and shoes set with customizable materials. It
resizes in MetaHuman Creator. This is the preferred next visible clothing step;
the separate fitted-mesh loader below remains useful for later custom pieces.

Download its `.mhpkg` from Fab, then run:

```powershell
python tools/unreal_import_techwear.py "C:\Users\Alexf\Downloads\oa_techwearoutfit.mhpkg"
```

The helper opens a full editor import session and targets
`/Game/Outfits/techwearOutfit`, the location required by the listing's texture
instructions. It refuses a populated destination. Inspect Unreal's import report;
successful discovery of the wardrobe item writes `Saved/Aura/techwear-import.json`
with the package checksum and source. Import is not a claim of successful fitting.

Next, add `WI_OA_techwearOutfit` to the preserved Aura character's Outfit Clothing
section in MetaHuman Creator, apply it, and assemble the same body proportions.
Do not change facial geometry or body size just to match the outfit. Check the
assembled materials, shoulders/hips/knees and body masking before enabling the
new look. This parametric route does not require entries in `[Aura.Wardrobe]`.

Keep the package, imported assets and assembly local under their Epic/Fab terms;
they are not MIT source assets. The importer has only been syntax/CLI checked
until the account download is available; actual import and fit remain pending.
See also Epic's [outfit workflow](https://dev.epicgames.com/documentation/metahuman/building-an-outfit-asset-in-unreal-engine).

## Asset contract

Create or fit the outfit around `SKM_AuraPrototype_Ada_BodyMesh`. Preserve its bone
names, parents and local rest transforms. Garments may omit unused branches, but
must keep the parent chain of each retained bone. Do not substitute an arbitrary
MetaHuman body size or assume matching bone names are enough.

The first target is a complete outfit matching the reference: fitted black top,
grey tactical trousers, substantial boots, straps and violet accents. Import the
parts as skeletal meshes under `/Game/Aura/Wardrobe` with their materials. Record
the creator, source, license and any redistribution limits beside the local asset
manifest. The source code's MIT license does not cover third-party art.

Add this to the local project's `Config/DefaultGame.ini` only after importing the
actual assets (the following paths are examples, not shipped assets):

```ini
[Aura.Wardrobe]
+Garments=/Game/Aura/Wardrobe/SK_Top.SK_Top
+Garments=/Game/Aura/Wardrobe/SK_Trousers.SK_Trousers
+Garments=/Game/Aura/Wardrobe/SK_Boots.SK_Boots
```

Restart the desktop host. All parts must load and match the body rig before the
assembled `SkeletalMesh` outfit component is hidden. Failure retains the original
outfit and logs the rejected asset and reason. `-AuraOriginalOutfit` bypasses the
replacement. Clear the config array to return to the default permanently.

## Current limits

This is a complete-outfit replacement, not separate top/bottom switching. Parts
follow the body's pose through Unreal's leader-pose mechanism; extra cloth bones,
independent cloth simulation and automatic body masking are unsupported. Fit the
geometry to prevent skin clipping and inspect shoulders, hips and knees in motion
before enabling an outfit. Rig compatibility alone does not establish visual fit,
material quality, weight quality or readiness for distribution.

The focused native check `Aura.Wardrobe.RigCompatibility` covers a fitted rig and
rejects foreign bones, changed proportions, changed parents and empty skeletons.
A real imported tactical garment remains necessary for end-to-end outfit signoff.

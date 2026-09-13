# Fitted wardrobe assets

The current local installation contains only MetaHuman's basic shirt and shorts.
No tactical jacket, trousers or boots have been added yet. The runtime now accepts
up to eight fitted skeletal garment parts without changing the animation adapter.

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

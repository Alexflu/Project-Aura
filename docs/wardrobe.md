# Fitted wardrobe assets

The local installation now contains Epic Techwear fitted and assembled onto the
existing Aura MetaHuman. It is a temporary jacket/trousers/shoes reference, not the
approved final design. The runtime also accepts up to eight fitted skeletal garment
parts without changing the animation adapter.

## Optional fitting reference: Epic Techwear

[Epic's MetaHuman Techwear Outfit](https://www.fab.com/listings/9e04c752-1979-4723-b78f-6d24afc532bc)
is a free parametric jacket, pants and shoes set with customizable materials. It
resizes in MetaHuman Creator. The user does not favor its appearance; it is only
an optional fitting reference, not the approved wardrobe direction. Prefer
separate customizable pieces matching the approved illustration.

On 2026-09-13, Fab in the installed Epic Games Launcher added the free asset to
its library and exposed Download only. The download then failed with
`FAB-FAB001` / `Unknown Error`. No usable package was obtained or imported.
Later that day, after updating and restarting Windows, the user downloaded
`oa_techwearoutfit.mhpkg` and `techwearbodypresets.zip` successfully using Chrome.
This removes the package-download blocker; it does not establish Windows Update
as the cause of the earlier failures. Do not repeat download troubleshooting.
The body-presets archive contains example G/H bodies, not required outfit parts;
do not apply those presets to Aura merely to use the outfit.

Download its `.mhpkg` from Fab, then run:

```powershell
python tools/unreal_import_techwear.py "C:\Users\Alexf\Downloads\oa_techwearoutfit.mhpkg"
```

The helper opens a full editor import session and targets
`/Game/Outfits/techwearOutfit`, the location required by the listing's texture
instructions. It refuses a populated destination. Inspect Unreal's import report;
successful discovery of the wardrobe item writes `Saved/Aura/techwear-import.json`
with the package checksum and source. Import is not a claim of successful fitting.

For a fresh character, drag `WI_OA_techwearOutfit` from the Content Drawer into
Hair & Clothing > Outfit Clothing, select it and click Wear. Select
`WI_DefaultGarment` and click Remove: wearing both causes the old shirt to
intersect the jacket. Save and assemble the same body proportions. Save the
generated character folder **and `/Game/MetaHumans/Common`** before launching
the host: assembly also creates shared groom textures and eyelash/fuzz materials.
Saving only the character folder leaves missing dependencies on a fresh launch.
Do not change facial geometry or body size just to match the outfit. Check the
assembled materials, shoulders/hips/knees and body masking before enabling the
new look. This parametric route does not require entries in `[Aura.Wardrobe]`.

Keep the package, imported assets and assembly local under their Epic/Fab terms;
they are not MIT source assets. On 2026-09-13, the full-editor import completed
with no messages in Unreal's Import Summary. It discovered
`WI_OA_techwearOutfit` at the required destination and wrote the local provenance
report. The downloaded package SHA-256 is
`3a552f031ef9430ed5fae643bde5a18b5545b71ed6f36dbccf19bb1bd08c4028`.
The local fitting and assembly completed on 2026-09-13; the generated assets were
saved and checked on 2026-09-14. The old garment was removed, clearing the visible
jacket overlap in Creator. No G/H body preset was applied and the rig was retained.
The previous authoring and assembled assets are backed up locally under
`Saved/Aura/Backups/pre-techwear`.

After assembly, run `py D:/Programs/Project-Aura/tools/unreal_audit_techwear.py`
in Unreal's console. It instantiates a temporary actor, checks the body/face and
jacket/pants/shoes materials, rejects a retained default garment, and writes
`Saved/Aura/techwear-assembly-audit.json`. The local actor passed with 342 body,
875 face and 342 outfit bones. This checks construction, not motion or visual fit.
The outfit exposes the existing charcoal/violet runtime palette parameters.
The desktop host was then launched with the saved assembly: it bound the layered
hair, applied the palette to 19 material slots and produced a live transparent
desktop surface. A clean relaunch after saving shared assets reported no missing
packages. The visible standing fit had no recurrence of the old-shirt overlap.
This is a limited local check; extreme poses, cloth dynamics, all LODs and the
approved final silhouette remain unfinished.
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

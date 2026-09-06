# Aura Rig 1 creator contract

This beta imports local **2D PNG layer rigs**, not arbitrary VRM, Live2D, FBX or 3D models. Visual design can vary; shared motions require compatible joints. The included `aura/assets/rig-reference/model.json` is a complete, original MIT reference pack. Its mannequin is a technical example; Aura's illustrated design remains the default.

## Author a pack

Copy the reference folder, replace its transparent PNG layers with your own licensed artwork, and edit `model.json`. Import that manifest through **Models → Import model.json**. Only validated manifest data and declared PNGs are copied to a content-addressed folder beside the local profile. Selection is currently session-only. Restart restores default Aura; copied artwork remains available for reimport.

The manifest has exactly these fields: `schema` (`aura-rig-1`), `id` (lowercase slug), `name`, `author`, `license`, `size` ([width, height]), `bones`, `layers`, and `sockets`. Attribution fields describe the creator's declaration; the importer cannot verify ownership.

- Bones: `name`, `parent`, `position` ([x,y] relative to parent), and `angle` (degrees). Declare root first, then parents before children. Positive angles rotate clockwise in screen coordinates. `root`, `chest` and `head` are required.
- Layers: `bone`, `asset` (a simple PNG filename beside the manifest), `pivot` (joint origin in image pixels), and `z` (paint order). All layers use the model's pixel coordinate system.
- Sockets: a map from names to `bone` and `position`. Supported names are `mouth`, `hand_right`, `holster_right`, `back`, `charm`, and `spell_origin`.

Bounds: 64 KB manifest, 1–48 joints, 1–48 layers, 20 sockets, 2048 pixels per image side, 4 MB per PNG, 16 million decoded pixels and 32 MB total PNG data. Unknown fields, scripts, URLs, nested asset paths, missing parents, cycles and nonfinite coordinates are rejected. Packs are data, never executable plugins.

## Compatibility tiers

Every valid pack supports idle and head inspection. Wave additionally needs `right_upper_arm`, `right_forearm` and `right_hand`. Optional `right_thumb`, `right_index`, `right_middle` and `right_ring` joints animate fingers.

Draw requires the right arm chain plus `hand_right` and `holster_right` sockets. Use the reference hierarchy and a downward, zero-angle bind pose: forearm and hand offsets have x=0 and positive y; the hand socket has x=0. A two-bone solve brings the hand to the holster, carries the equipped prop, then returns it. Unsupported shapes should omit the capability rather than promise correct contact. Fit, reach, clipping, layer occlusion and clothing proportions still need creator review. Reduced motion freezes the pose.

Arbitrary extra joints and artwork are allowed within limits, but they do not automatically gain shared animations. Apparel is not yet a swappable layer-pack format. Existing inventory imports describe procedural items and spells. Future mesh/VRM adapters need their own versioned profile, expression mapping, attachment rules and validation; they must not silently reinterpret this format.

Connected MCP clients can propose `wave`, `inspect` or `draw` through `aura_propose_cue`. Each still requires local approval and a currently selected compatible rig. Draw is a complete draw-and-stow cycle; persistent reveal/stow remains specific to the illustrated renderer.

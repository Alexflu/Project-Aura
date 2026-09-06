> Updated in 0.6: procedural equipment slots and creator item variants are implemented. See [current format](creator-items-v1.md). The broader rigged apparel/model design below remains planned.

# Creator inventory and equipment — proposed design

Status: design specification, not a functioning inventory in 0.5. The Shift wheel is implemented for existing controls; equipment editing comes after attachment points and a proper rig.

## Everyday interface

Aura can normally live on the desktop. Hold a modifier over her to reveal a small action wheel; use it for voice, expression, equipment, spellbook, and settings. Keep Studio as an optional detailed editor, not a required always-visible setup page. The current wheel uses Shift while the pointer is over Aura. An eventual user-configurable hotkey can open Studio without a global text-recording keyboard hook.

## Inventory model

Separate owned/available content from currently equipped items. Slots: hair, head, neck, torso, outerwear, hands, legs, feet, waist, back, holster-left/right, bag, and accessories. Weapons/tools attach to sockets; a hidden dagger occupies a holster/bag socket with stowed and drawn states. A spellbook contains learned/available visual spells and a small active loadout. Use presets to switch entire outfits/loadouts and retain per-slot overrides.

User-selected arsenal is authoritative. Personal tastes may guide suggestions but must not silently remove favorite items or add unwanted ones. Locked slots, compatible layering, color channels, undo, missing-asset fallback, and a neutral pose are required. Apparel should deform with its owning body segment; straps, hair, loose cloth and hanging props can have bounded secondary movement. Drawing an item needs authored hand/arm poses and occlusion, not just moving a flat icon.

## Creator packs

Versioned declarative content, with no executable Python/JavaScript in ordinary item packs. A pack should identify its creator, license/attribution, compatible rig version, asset paths, slot/socket requirements, layer order, palette channels, previews, animation clips, fallback pose, and dependencies. Custom models are a separate pack type with a declared skeleton/socket map; a model cannot silently claim compatibility with every outfit.

A future importer should validate paths stay inside the selected pack, file dimensions/byte sizes, allowed media types, bounds/pivots, clip duration/frame count, dependency cycles and compatibility. Show an import preview and report unsupported parts. Packs cannot grant app access or bypass the existing task approval system. Content should work locally first; a community catalog can be added without making an account mandatory.

## Practical first vertical slice

One original hand-held prop and its holster, stow/draw animations, equip/unequip/undo, and a small inventory pane opened from the wheel. Then one interchangeable outerwear item, and one spell with anticipation/cast/recovery/cancel clips. Publish a documented sample pack and validator so contributors can author against a stable example. Expand to the arsenal, arcane, blademaster and mecha families described in power-styles.md.

# Creator items, format 1

This format is implemented in beta 0.6. Copy an example from examples/creator-items, edit the JSON and choose Equipment → Import creator item. Import adds an available item; equipping it is a separate choice. Equipment persists across restarts and supports 20 session undo steps.

Every field below is required; unknown fields are rejected. No scripts, paths, URLs or external assets are loaded.

```json
{
  "schema": 1,
  "id": "yourname.frost-dagger",
  "name": "Frost dagger",
  "slot": "holster",
  "kind": "dagger",
  "color": "#88DDFF",
  "author": "Your name",
  "license": "MIT"
}
```

IDs: 3–64 lowercase letters, digits, dot, hyphen or underscore, beginning with a letter. The aura. namespace is reserved. Name, author and license: 1–100 printable characters. Colors: #RRGGBB. Maximum file size: 8 KB; at most 64 imported items. A duplicate ID is rejected rather than replacing someone else's item.

| Kind | Slot | Current behavior |
| --- | --- | --- |
| dagger | holster | Blade with a floating reveal/stow animation |
| bag | back | Cross-body satchel with subtle sway |
| crystal | charm | Floating arcane focus |
| fire | spell | Ember spiral particles |
| ice | spell | Frost shards and rings |
| lightning | spell | Animated branching lines |

Only one item per slot is equipped. Equipping another replaces that slot; selecting the equipped item removes it. Cast spell plays a bounded visual effect without changing files or applications. Effects respect Pause and Reduce motion.

This first format customizes Aura's built-in shapes and effects. It is not an arbitrary asset/model importer. Separate apparel meshes, custom art, skeletal animation, hand grips and authored spell clips need a later rig-aware pack format. Do not label a color variant as a new model.

Built-in items and supplied examples use MIT. For submitted items, include accurate attribution and a license you can grant. Contributor tests are in tests/test_equipment_showcase.py.

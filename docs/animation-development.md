# Beta 10 avatar movement refinement

In beta 10, select a layered model and use Models → Stretch. Compatible
models need both upper-arm and forearm roles. The gesture blends back to idle;
missing roles leave it unavailable rather than imposing an incompatible pose.

Idle arms now follow breathing. Dance includes coordinated wrist and ankle motion.
Headbanging offsets the torso timing from the head. Optional hair_, cloth_ and
gear_ joints follow music with delayed, bounded motion. These are procedural
offsets, not cloth collision physics. Existing Aura Rig 1 packs remain compatible.

Run `python tools/export_movement_preview.py` for a preview using the actual
renderer with simulated music levels. These movements are included in the portable beta. The default single-image avatar does
not gain articulated limbs; choose the illustrated rig or a compatible creator rig.

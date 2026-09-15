"""Run inside Unreal Editor Python to bind a supported installed groom to Aura.

Creates local assets only; Epic content remains subject to its original license.
"""
import json
import os
from pathlib import Path
import unreal

STYLE = os.environ.get("AURA_HAIR_STYLE", "Hair_M_Layered")
if STYLE not in ("Hair_M_Layered", "Hair_M_BobMessy"):
    raise RuntimeError(f"Unsupported installed hairstyle: {STYLE}")
SOURCE = f"/MetaHumanCharacter/Optional/Grooms/GroomAssets/Hair/{STYLE}/{STYLE}"
REFERENCE = f"/MetaHumanCharacter/Optional/Grooms/Bindings/Hair/{STYLE}_Binding"
TARGET = "/Game/MetaHumans/AuraPrototype_Ada/Face/SKM_AuraPrototype_Ada_FaceMesh"
GROOM = f"/Game/Aura/Appearance/{STYLE}"
BINDING = f"/Game/Aura/Appearance/{STYLE}_Binding"

assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
source = unreal.load_asset(SOURCE)
reference = unreal.load_asset(REFERENCE)
target = unreal.load_asset(TARGET)
if not all((source, reference, target)):
    raise RuntimeError("Install MetaHuman Creator Core Data and assemble Aura's face first")
source_mesh = reference.get_editor_property("source_skeletal_mesh") or reference.get_editor_property("target_skeletal_mesh")
if source_mesh is None:
    raise RuntimeError("The installed groom has no reference head for fitting")
groom = assets.load_asset(GROOM) if assets.does_asset_exist(GROOM) else assets.duplicate_asset(SOURCE, GROOM)
if groom is None:
    raise RuntimeError(f"Could not copy {STYLE}")
binding = assets.load_asset(BINDING) if assets.does_asset_exist(BINDING) else unreal.GroomLibrary.create_new_groom_binding_asset_with_path(
    BINDING, groom, target, 100, source_mesh, 0)
if (binding is None or binding.get_editor_property("target_skeletal_mesh") != target
        or binding.get_editor_property("groom") != groom
        or binding.get_editor_property("source_skeletal_mesh") != source_mesh):
    raise RuntimeError("Missing or incompatible local binding; preserve and inspect the existing asset")
for path in (GROOM, BINDING):
    if not assets.save_asset(path, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {path}")
report = dict(source=SOURCE, reference_head=source_mesh.get_path_name(), target=TARGET,
              groom=GROOM, binding=BINDING, license="Epic content; not repository MIT",
              limits="Local editor dependency; final styling, physics and packaged asset migration remain open")
manifest_name = "layered-hair-manifest.json" if STYLE == "Hair_M_Layered" else "messy-bob-hair-manifest.json"
destination = Path(unreal.Paths.project_saved_dir()) / "Aura" / manifest_name
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("AURA_PREPARED_HAIR: " + json.dumps(report))

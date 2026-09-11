"""Run inside Unreal: verify the assembled prototype's body and face components.

This instantiates a temporary actor without saving a level or changing the demo.
It does not assert animation, lip sync, or likeness to the approved Aura design.
"""
import json
from pathlib import Path
import unreal

ROOT = "/Game/MetaHumans"
NAME = "BP_AuraPrototype_Ada"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([ROOT], force_rescan=True)
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
matches = [p for p in assets.list_assets(ROOT, recursive=True, include_folder=False)
           if p.rsplit("/", 1)[-1].split(".")[0] == NAME]
if len(matches) != 1:
    raise RuntimeError(f"Expected one assembled {NAME}; found {matches}. Assemble and save in MetaHuman Creator first.")
actor_class = unreal.EditorAssetLibrary.load_blueprint_class(matches[0])
if actor_class is None:
    raise RuntimeError("Assembled character Blueprint could not load")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = actors.spawn_actor_from_class(actor_class, unreal.Vector(0, 0, 0), transient=True)
if actor is None:
    raise RuntimeError("Assembled character could not be instantiated")
try:
    components = []
    for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        components.append({"name": component.get_name(), "bones": component.get_num_bones()})
    for required in ("body", "face"):
        if not any(c["name"].lower() == required and c["bones"] > 20 for c in components):
            raise RuntimeError(f"Missing loaded skeletal {required}: {components}")
    report = {"result": "passed", "blueprint": matches[0], "components": components,
              "limits": "Asset construction only; animation, voice and Aura likeness are not validated."}
    destination = Path(unreal.Paths.project_saved_dir()) / "Aura/metahuman-audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("AURA_METAHUMAN_AUDIT: " + json.dumps(report))
finally:
    actors.destroy_actor(actor)

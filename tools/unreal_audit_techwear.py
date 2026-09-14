"""Run inside Unreal after fitting and assembling Techwear in MetaHuman Creator.

Inspects the actual assembled actor; does not establish visual fit or cloth quality.
"""
import json
from pathlib import Path
import unreal

blueprint = "/Game/MetaHumans/AuraPrototype_Ada/BP_AuraPrototype_Ada"
actor_class = unreal.EditorAssetLibrary.load_blueprint_class(blueprint)
if actor_class is None:
    raise RuntimeError("Assemble and save AuraPrototype_Ada first")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = actors.spawn_actor_from_class(actor_class, unreal.Vector(), transient=True)
if actor is None:
    raise RuntimeError("Could not instantiate the assembled character")
try:
    components = []
    for component in actor.get_components_by_class(unreal.MeshComponent):
        materials = []
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            if material:
                materials.append({
                    "path": material.get_path_name(),
                    "vectors": [str(name) for name in
                                unreal.MaterialEditingLibrary.get_vector_parameter_names(material)],
                })
        row = {"name": component.get_name(), "class": component.get_class().get_name(),
               "materials": materials}
        if isinstance(component, unreal.SkeletalMeshComponent):
            row["bones"] = component.get_num_bones()
        components.append(row)
    material_paths = " ".join(m["path"].lower() for c in components for m in c["materials"])
    missing = [part for part in ("jacket", "pants", "shoes") if part not in material_paths]
    if missing:
        raise RuntimeError(f"Assembled Techwear materials missing: {missing}")
    if "defaultgarment" in material_paths or "m_dg_" in material_paths:
        raise RuntimeError("Default garment still present; remove it before assembling Techwear")
    for name in ("body", "face"):
        if not any(c["name"].lower() == name and c.get("bones", 0) > 20 for c in components):
            raise RuntimeError(f"Missing loaded skeletal {name}")
    report = {"result": "passed", "blueprint": blueprint, "components": components,
              "limits": "Construction and material presence only; inspect motion, masking and fit in the host."}
    output = Path(unreal.Paths.project_saved_dir()) / "Aura/techwear-assembly-audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("AURA_TECHWEAR_ASSEMBLY_AUDIT: " + json.dumps(report))
finally:
    actors.destroy_actor(actor)

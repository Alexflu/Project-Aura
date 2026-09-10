"""Run inside Unreal Editor Python: prepare a local, editable MetaHuman preset.

This does not request cloud rigging, assemble a runtime character, or choose Aura's
final appearance. The installed Epic Ada preset is only an authoring starting point.
"""
import unreal

SOURCE = "/MetaHumanCharacter/Optional/Presets/Ada"
TARGET = "/Game/Aura/Characters/AuraPrototype_Ada"
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(["/MetaHumanCharacter/Optional/Presets", "/Game/Aura"], force_rescan=True)

if not assets.does_asset_exist(TARGET):
    source = assets.load_asset(SOURCE)
    if source is None:
        raise RuntimeError("Install MetaHuman Creator Core Data and enable MetaHuman Creator")
    asset = assets.duplicate_asset(SOURCE, TARGET)
    if asset is None:
        raise RuntimeError("Could not duplicate the local preset")
    if not assets.save_asset(TARGET):
        raise RuntimeError("Could not save the authoring asset")
else:
    asset = assets.load_asset(TARGET)
unreal.log("AURA_METAHUMAN_PREPARED: " + asset.get_path_name())

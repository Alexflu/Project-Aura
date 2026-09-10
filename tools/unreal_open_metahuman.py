"""Run inside the full Unreal Editor to open the preserved local authoring asset."""
from pathlib import Path
import runpy
import unreal

prepared = runpy.run_path(str(Path(__file__).with_name("unreal_prepare_metahuman.py")))
asset = prepared["asset"]
editor = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
if not editor.open_editor_for_assets([asset]):
    raise RuntimeError("MetaHuman editor did not open; inspect the Unreal Output Log")
unreal.log("AURA_METAHUMAN_EDITOR_OPEN: " + asset.get_path_name())

"""Full-editor script; use unreal_import_techwear.py to select the package."""
import hashlib
import json
import os
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
package = Path(os.environ["AURA_TECHWEAR_PACKAGE"])
destination = "/Game/Outfits/techwearOutfit"
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
if assets.list_assets(destination, recursive=True, include_folder=False):
    raise RuntimeError("Techwear destination already contains assets. Inspect them in Unreal before replacing anything.")
assets.make_directory(destination)
task = unreal.AssetImportTask()
task.filename = str(package)
task.destination_path = destination
task.replace_existing = False
task.automated = False
task.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = assets.list_assets(destination, recursive=True, include_folder=False)
wardrobe = [path for path in paths if path.rsplit("/", 1)[-1].lower().startswith("wi_") and "techwear" in path.lower()]
if not wardrobe:
    raise RuntimeError("No wardrobe item found after import. Inspect the MetaHuman import report; fitting has not been performed.")
with package.open("rb") as source_file:
    digest = hashlib.file_digest(source_file, "sha256").hexdigest()
report = {
    "source": "https://www.fab.com/listings/9e04c752-1979-4723-b78f-6d24afc532bc",
    "package": package.name,
    "sha256": digest,
    "destination": destination,
    "wardrobe_items": wardrobe,
    "status": "imported; not yet fitted or assembled",
    "license": "Epic/Fab asset terms; not repository MIT; retain download license receipt",
}
output = Path(unreal.Paths.project_saved_dir()) / "Aura/techwear-import.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.EditorAssetLibrary.sync_browser_to_objects(wardrobe)
unreal.log("AURA_TECHWEAR_IMPORTED: " + json.dumps(report))

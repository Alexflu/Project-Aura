"""Open Unreal to import the user-downloaded Epic Techwear package locally."""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.unreal_body import PROJECT, ROOT, editor_path, installed_engine, runtime_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Downloaded oa_techwearoutfit.mhpkg")
    parser.add_argument("--engine-root", type=Path)
    args = parser.parse_args()
    package = args.package.resolve(strict=True)
    if package.suffix.lower() != ".mhpkg" or not zipfile.is_zipfile(package):
        parser.error("Select the .mhpkg download, not a web page or outer ZIP")
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if not any(Path(name).name.lower() == "manifest.json" for name in names):
            parser.error("Package has no MetaHuman manifest")
    env = runtime_environment()
    env["AURA_TECHWEAR_PACKAGE"] = str(package)
    command = [str(editor_path(args.engine_root or installed_engine())), str(PROJECT),
               "-NoSplash", f"-ExecutePythonScript={ROOT / 'tools/unreal_import_techwear_editor.py'}"]
    process = subprocess.Popen(command, env=env)
    print(f"Opened Unreal import session ({process.pid}); follow the import report in the editor.")


if __name__ == "__main__":
    main()

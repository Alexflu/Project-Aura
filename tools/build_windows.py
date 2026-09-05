"""Build an unsigned portable Windows beta; never installs or starts it."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
                "--noupx", "--name", "ProjectAura", "launch_desktop.py"], cwd=ROOT, check=True)
bundle = ROOT / "dist" / "ProjectAura"
for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / filename, bundle / filename)
shutil.copytree(ROOT / "docs", bundle / "docs", dirs_exist_ok=True)
licenses = bundle / "licenses"
licenses.mkdir(exist_ok=True)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if not python_license.exists():
    raise RuntimeError("Python license not found; package must include dependency notices")
shutil.copy2(python_license, licenses / "Python.txt")
import PyInstaller
import importlib.metadata
dist = importlib.metadata.distribution("pyinstaller")
for file in dist.files or []:
    if file.name == "COPYING.txt":
        shutil.copy2(dist.locate_file(file), licenses / "PyInstaller-COPYING.txt")
shutil.copy2(ROOT / "third_party" / "Tcl-license.txt", licenses / "Tcl-license.txt")
# Tcl/Tk license files are distributed with the installed Python runtime.
for file in (Path(sys.base_prefix) / "tcl").rglob("license.terms"):
    shutil.copy2(file, licenses / (file.parent.name + "-license.txt"))
artifact = ROOT / "artifacts" / "ProjectAura-0.1.0-beta.1-windows-x64.zip"
artifact.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(bundle.rglob("*")):
        if file.is_file():
            archive.write(file, Path("ProjectAura") / file.relative_to(bundle))
digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
artifact.with_suffix(".zip.sha256").write_text(f"{digest}  {artifact.name}\n", encoding="utf-8")
print(json.dumps({"artifact": str(artifact), "sha256": digest, "bytes": artifact.stat().st_size}))

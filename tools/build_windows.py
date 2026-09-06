"""Build an unsigned portable Windows beta; never installs or starts it."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
                "--add-data", "aura/assets;aura/assets", "--hidden-import", "pystray._win32", "--collect-submodules", "comtypes", "--noupx", "--name", "ProjectAura", "launch_desktop.py"], cwd=ROOT, check=True)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--console",
                "--copy-metadata", "mcp", "--collect-data", "mcp", "--hidden-import", "anyio._backends._asyncio", "--noupx", "--name", "AuraMCP", "launch_mcp.py"], cwd=ROOT, check=True)
bundle = ROOT / "dist" / "ProjectAura"
shutil.copytree(ROOT / "dist" / "AuraMCP", bundle / "bridge", dirs_exist_ok=True)
for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / filename, bundle / filename)
shutil.copytree(ROOT / "docs", bundle / "docs", dirs_exist_ok=True)
shutil.copytree(ROOT / "examples", bundle / "examples", dirs_exist_ok=True)
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
pillow_dist = importlib.metadata.distribution("pillow")
for file in pillow_dist.files or []:
    if file.name == "LICENSE" and "dist-info" in str(file):
        shutil.copy2(pillow_dist.locate_file(file), licenses / "Pillow-LICENSE.txt")
shutil.copy2(ROOT / "third_party" / "Tcl-license.txt", licenses / "Tcl-license.txt")
# Tcl/Tk license files are distributed with the installed Python runtime.
for file in (Path(sys.base_prefix) / "tcl").rglob("license.terms"):
    shutil.copy2(file, licenses / (file.parent.name + "-license.txt"))
# Preserve metadata and license texts for the portable bridge's dependency closure.
from packaging.requirements import Requirement
pending, seen = ["mcp", "pystray", "pycaw"], set()
# Optional imports may be present in the build environment. Include notices for
# distributions actually frozen by PyInstaller, not just declared root packages.
import ast
package_owners = importlib.metadata.packages_distributions()
def collect_owners(value):
    if isinstance(value, (tuple, list)):
        if len(value) == 3 and isinstance(value[0], str) and isinstance(value[2], str) and value[2] in ("PYMODULE", "EXTENSION", "PYSOURCE"):
            pending.extend(package_owners.get(value[0].split(".")[0], ()))
        for child in value:
            collect_owners(child)
for name in ("ProjectAura", "AuraMCP"):
    collect_owners(ast.literal_eval((ROOT / "build" / name / "Analysis-00.toc").read_text(encoding="utf-8")))
while pending:
    name = pending.pop()
    if name.lower() in seen:
        continue
    seen.add(name.lower())
    dependency = importlib.metadata.distribution(name)
    directory = licenses / dependency.metadata["Name"]
    directory.mkdir(exist_ok=True)
    (directory / "METADATA.txt").write_text((dependency.read_text("METADATA") or dependency.metadata["Name"]), encoding="utf-8")
    for file in dependency.files or []:
        if "dist-info" in str(file) and any(word in file.name.lower() for word in ("license", "copying", "notice")):
            parts = Path(str(file)).parts
            marker = next(i for i, part in enumerate(parts) if part.endswith(".dist-info"))
            target = directory.joinpath(*parts[marker + 1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dependency.locate_file(file), target)
    for spec in dependency.requires or []:
        requirement = Requirement(spec)
        if not requirement.marker or requirement.marker.evaluate({"extra": ""}):
            pending.append(requirement.name)
# Include the exact LGPL tray library sources so recipients can modify/rebuild it.
tray_dist = importlib.metadata.distribution("pystray")
for file in tray_dist.files or []:
    if str(file).replace("\\", "/").startswith("pystray/") and str(file).endswith(".py"):
        target = licenses / "pystray" / "source" / str(file)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tray_dist.locate_file(file), target)
(licenses / "pystray" / "REBUILD.txt").write_text(
    "Unmodified pystray 0.19.5 sources and GPL/LGPL notices are included. "
    "To use a modified version, obtain Project Aura's matching source release, "
    "install its build dependencies, replace pystray in that environment with your "
    "modified sources, and run python tools/build_windows.py. "
    "Project Aura imposes no additional restriction on modifying or debugging this library.\n",
    encoding="utf-8")
artifact = ROOT / "artifacts" / "ProjectAura-0.7.0-beta.3-windows-x64.zip"
artifact.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(bundle.rglob("*")):
        if file.is_file():
            archive.write(file, Path("ProjectAura") / file.relative_to(bundle))
digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
artifact.with_suffix(".zip.sha256").write_text(f"{digest}  {artifact.name}\n", encoding="utf-8")
print(json.dumps({"artifact": str(artifact), "sha256": digest, "bytes": artifact.stat().st_size}))

"""Prepare locally licensed mannequin assets, build, or run the Unreal body."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "unreal/AuraBody/AuraBody.uproject"


def installed_engine():
    override = os.environ.get("AURA_UNREAL_ROOT")
    if override:
        return Path(override)
    manifest = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Epic/UnrealEngineLauncher/LauncherInstalled.dat"
    if manifest.is_file():
        for entry in json.loads(manifest.read_text(encoding="utf-8"))["InstallationList"]:
            if entry.get("AppName") == "UE_5.6":
                return Path(entry["InstallLocation"])
    raise FileNotFoundError("Install Unreal 5.6 or supply --engine-root / AURA_UNREAL_ROOT")


def editor_path(engine):
    path = engine / "Engine/Binaries/Win64/UnrealEditor.exe"
    if not path.is_file():
        raise FileNotFoundError(f"Unreal Editor not installed at {path}")
    return path


def runtime_environment():
    env = os.environ.copy()
    env["UE-LocalDataCachePath"] = str(PROJECT.parent / "DerivedDataCache")
    return env


def prepare(engine):
    """Copy the engine template's Characters tree without replacing local edits."""
    candidates = sorted((engine / "Templates/TemplateResources/High/Characters").rglob("SKM_Quinn_Simple.uasset"))
    if not candidates:
        raise FileNotFoundError("Install Unreal's Templates and Feature Packs; SKM_Quinn_Simple was not found under Templates")
    source = next((parent for parent in candidates[0].parents if parent.name == "Content"), None)
    if source is None:
        raise ValueError(f"Unexpected mannequin layout: {candidates[0]}")
    destination = PROJECT.parent / "Content/Characters"
    inventory = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise FileExistsError(f"Preserving different local asset: {target}")
        inventory.append({"path": relative.as_posix(), "sha256": digest})
    # Validate the whole copy first, so a conflict never leaves a partial import.
    for entry in inventory:
        relative = Path(entry["path"])
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source / relative, target)
    manifest = PROJECT.parent / "Saved/Aura/asset-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"source": str(source), "license": "Epic Unreal Engine EULA; not repository MIT",
                                   "assets": inventory}, indent=2), encoding="utf-8")
    print(f"Prepared {len(inventory)} local template files. Provenance: {manifest}")


def launch_command(engine):
    return [str(editor_path(engine)), str(PROJECT), "-game", "-windowed", "-ResX=1280", "-ResY=720",
            "-NoSplash", "-NoSound", "-ExecCmds=t.MaxFPS 60"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "build", "run", "demo", "prepare-metahuman"))
    parser.add_argument("--engine-root", type=Path)
    args = parser.parse_args()
    engine = (args.engine_root or installed_engine()).resolve()
    editor_path(engine)
    if args.action == "prepare":
        prepare(engine)
    elif args.action == "build":
        command = [str(engine / "Engine/Build/BatchFiles/Build.bat"), "AuraBodyEditor", "Win64",
                   "Development", f"-Project={PROJECT}", "-WaitMutex", "-NoHotReloadFromIDE"]
        subprocess.run(command, env=runtime_environment(), check=True)
    elif args.action == "prepare-metahuman":
        command = [str(engine / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"), str(PROJECT),
                   "-run=pythonscript", f"-script={ROOT / 'tools/unreal_prepare_metahuman.py'}", "-Unattended", "-NullRHI"]
        subprocess.run(command, env=runtime_environment(), check=True)
    elif args.action == "demo":
        folder = PROJECT.parent / "Saved/Aura/Demos" / uuid.uuid4().hex[:10]
        folder.mkdir(parents=True)
        process = subprocess.Popen(launch_command(engine) + ["-AuraTelemetry", f"-AuraDataDir={folder}"], env=runtime_environment())
        try:
            deadline = time.monotonic() + 180
            telemetry = folder / "runtime.jsonl"
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Unreal closed before the stage was ready")
                if telemetry.is_file():
                    lines = telemetry.read_text(encoding="utf-8").splitlines(keepends=True)
                    complete = [line for line in lines if line.endswith("\n")]
                    if complete and json.loads(complete[-1])["rig_ready"]:
                        break
                time.sleep(.25)
            else:
                raise RuntimeError("Stage did not become ready; run prepare and build first")
            subprocess.run([sys.executable, str(ROOT / "tools/skeleton_zero.py"), "--output", str(folder / "behavior.json")], check=True)
            print("Replay finished. The offline stage will remain open until you close it.", flush=True)
            process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
    else:
        print("Opening a visible offline Unreal stage. Start tools/skeleton_zero.py to send cues.")
        subprocess.run(launch_command(engine), env=runtime_environment(), check=True)


if __name__ == "__main__":
    main()

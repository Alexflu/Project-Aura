"""Speak local text through Windows audio and the assembled MetaHuman jaw."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.embodied_speech import EmbodiedSpeech
from aura.embodiment import write_snapshot
from tools.unreal_body import PROJECT, installed_engine, launch_command, runtime_environment


def last_sample(path):
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    complete = [line for line in lines if line.endswith("\n")]
    return json.loads(complete[-1]) if complete else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Local speech, 1 to 1000 characters")
    parser.add_argument("--engine-root", type=Path)
    args = parser.parse_args()
    if not args.text.strip() or len(args.text) > 1000:
        parser.error("Text must contain 1 to 1000 characters")
    folder = PROJECT.parent / "Saved/Aura/Speech" / uuid.uuid4().hex[:10]
    folder.mkdir(parents=True)
    output = folder / "behavior.json"
    bridge = EmbodiedSpeech()
    engine = args.engine_root or installed_engine()
    command = launch_command(engine, metahuman=True) + ["-AuraSpeechAudio", "-AuraTelemetry", f"-AuraDataDir={folder}"]
    process = subprocess.Popen(command, env=runtime_environment())
    try:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Unreal closed before speech could start")
            write_snapshot(output, bridge.snapshot(.05))
            sample = last_sample(folder / "metahuman-runtime.jsonl")
            if sample and sample["connected"]:
                break
            time.sleep(.05)
        else:
            raise RuntimeError("MetaHuman did not connect; assemble, audit and build first")
        print("Local Windows speech; volume-driven jaw, not phoneme lip sync. Ctrl+C stops playback.", flush=True)
        bridge.speak(args.text)
        started = time.monotonic()
        while bridge.speech.state != "idle":
            if process.poll() is not None:
                raise RuntimeError("Unreal closed; stopping speech")
            sample_path = folder / "metahuman-runtime.jsonl"
            # Stop audible playback if the renderer stalls or loses this stream.
            sample = last_sample(sample_path)
            if not sample or time.time() - sample_path.stat().st_mtime > 1.5 or not sample["connected"]:
                raise RuntimeError("Renderer connection lost; stopping speech")
            if time.monotonic() - started > 110:
                raise RuntimeError("Local speech session reached its time limit")
            write_snapshot(output, bridge.snapshot(1 / 30))
            time.sleep(1 / 30)
        print(f"Playback complete. Runtime evidence: {folder}", flush=True)
    finally:
        bridge.stop()
        try:
            write_snapshot(output, bridge.snapshot(0))
            # Let the renderer consume the closed-mouth state before shutdown.
            time.sleep(.15)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Speech stopped.")

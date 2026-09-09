"""Replay authored cues into Unreal's local state file; no voice or AI is simulated as live."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.embodiment import BehaviorController, number, validate_command, write_snapshot

ROOT = Path(__file__).resolve().parents[1]


def load_timeline(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not 1 <= len(data) <= 256:
        raise ValueError("Timeline requires 1..256 cues")
    previous = -1.0
    ids = set()
    for entry in data:
        if not isinstance(entry, dict) or set(entry) != {"at_s", "command"}:
            raise ValueError("Expected at_s and command")
        at = number(entry["at_s"], 0, 300)
        if at < previous:
            raise ValueError("Timeline must be sorted")
        previous = at
        cmd = validate_command(entry["command"])
        if cmd["id"] in ids:
            raise ValueError("Timeline command ids must be unique")
        ids.add(cmd["id"])
    return data


def replay(timeline, output, fast=False):
    controller = BehaviorController()
    index = 0
    frames = int((timeline[-1]["at_s"] + 2) * 30) + 1
    deadline = time.monotonic()
    try:
        for frame in range(frames):
            elapsed = frame / 30
            while index < len(timeline) and timeline[index]["at_s"] <= elapsed:
                command = timeline[index]["command"]
                print(f"{elapsed:5.2f}s {command['action']}: {controller.apply(command)}", flush=True)
                index += 1
            write_snapshot(output, controller.snapshot())
            controller.tick(1 / 30)
            if not fast:
                deadline += 1 / 30
                time.sleep(max(0, deadline - time.monotonic()))
    finally:
        controller.stop()
        write_snapshot(output, controller.snapshot())
    return controller


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, default=ROOT / "examples/skeleton-zero/timeline.json")
    parser.add_argument("--output", type=Path, default=ROOT / "unreal/AuraBody/Saved/Aura/behavior.json")
    parser.add_argument("--fast", action="store_true", help="Offline validation only; skips real-time pacing")
    args = parser.parse_args()
    print("AUTHORED OFFLINE DEMO: mouth cue only, no audio, microphone, camera or cloud connection.")
    replay(load_timeline(args.timeline), args.output, args.fast)

"""Launch the real Unreal stage and check its receiver/rig telemetry end to end."""
import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.embodiment import BehaviorController, write_snapshot
from tools.skeleton_zero import load_timeline, replay
from tools.unreal_body import PROJECT, ROOT, launch_command, runtime_environment


def read_samples(path):
    if not path.exists():
        return []
    # Only complete lines: the renderer may still be appending its next sample.
    text = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines(keepends=True) if line.endswith("\n")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--metahuman", action="store_true")
    parser.add_argument("--rebuild-retarget-cache", action="store_true", help="Development comparison: rebuild skeleton mappings every frame")
    args = parser.parse_args()
    folder = PROJECT.parent / "Saved/Aura/Smoke" / uuid.uuid4().hex[:10]
    folder.mkdir(parents=True)
    snapshot = folder / "behavior.json"
    telemetry = folder / "runtime.jsonl"
    controller = BehaviorController()
    controller.apply({"version": 1, "id": "stale-speech", "action": "speak", "params": {"duration_s": 10}})
    write_snapshot(snapshot, controller.snapshot())
    command = launch_command(args.engine_root, args.metahuman) + ["-Unattended", "-AuraTelemetry", f"-AuraDataDir={folder}"]
    if args.rebuild_retarget_cache:
        command.append("-AuraRebuildRetargetCache")
    process = subprocess.Popen(command, env=runtime_environment())
    try:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Unreal exited with {process.returncode}; inspect Saved/Logs")
            samples = read_samples(telemetry)
            if samples and samples[-1]["rig_ready"] and samples[-1]["elapsed_s"] >= 2:
                break
            time.sleep(.25)
        else:
            raise RuntimeError("No ready skeletal rig within 180 seconds; inspect Saved/Logs")
        assert not any(s["connected"] or s["mouth"] for s in samples), "Static leftover snapshot animated"
        print("PASS static leftover snapshot is ignored; real skeletal mesh loaded", flush=True)
        replay(load_timeline(ROOT / "examples/skeleton-zero/timeline.json"), snapshot)
        time.sleep(1.5)
        samples = read_samples(telemetry)
        assert all(s["rig_ready"] and s["bones"] > 20 for s in samples)
        assert {s["mode"] for s in samples} >= {"idle", "listening", "speaking"}
        assert any(s["wave_weight"] > .7 for s in samples), "No skeletal wave response"
        assert max(s["right_hand_z"] for s in samples) - min(s["right_hand_z"] for s in samples) > 30, "Wrist bone did not move"
        assert max(s["left_foot_z"] for s in samples) - min(s["left_foot_z"] for s in samples) > 3, "Foot bone did not move"
        assert any(abs(s["head_yaw"]) > 15 for s in samples), "No gaze response"
        assert max(s["x"] for s in samples) > 180, "No stage movement"
        assert any(s["mouth"] > .1 for s in samples), "No synthetic speech cue"
        assert not samples[-1]["connected"] and samples[-1]["mouth"] == 0, "Stale producer did not idle"
        assert abs(samples[-1]["x"] - samples[-3]["x"]) < .01, "Stale producer did not hold position"
        # Reconnect, then corrupt input during active motion/speech.
        controller = BehaviorController()
        controller.apply({"version": 1, "id": "move", "action": "walk_to", "params": {"x": 400, "y": 0}})
        controller.apply({"version": 1, "id": "speak", "action": "speak", "params": {"duration_s": 10}})
        for _ in range(30):
            write_snapshot(snapshot, controller.snapshot())
            controller.tick(1 / 30)
            time.sleep(1 / 30)
        assert read_samples(telemetry)[-1]["connected"], "Producer restart failed"
        write_snapshot(snapshot, {"invalid": True})
        time.sleep(1.5)
        tail = read_samples(telemetry)[-3:]
        assert all(not s["connected"] and s["mouth"] == 0 for s in tail)
        assert max(s["x"] for s in tail) - min(s["x"] for s in tail) < .01
        ms = [s["frame_ms"] for s in samples if s["elapsed_s"] > 3]
        report = {"result": "passed", "samples": len(samples), "bones": samples[-1]["bones"],
                  "sampled_mean_frame_ms": statistics.mean(ms), "sampled_worst_frame_ms": max(ms),
                  "checks": ["skeletal_mesh", "static_leftover", "six_cue_channels", "producer_restart",
                             "stale_disconnect", "malformed_input_stop"],
                  "limits": "Sampled frame times; offline cues; mannequin has no facial rig or audio."}
        if args.metahuman:
            meta = read_samples(folder / "metahuman-runtime.jsonl")
            assert meta, "MetaHuman adapter did not start; mannequin fallback is not a pass"
            for key in ("body_cache_builds", "face_cache_builds"):
                count = meta[-1][key]
                expected = count > 10 if args.rebuild_retarget_cache else count == 1
                assert expected, f"Unexpected {key}: {count}"
            warm = [s for s in meta if s["elapsed_s"] > 3]
            report["retarget_pose_mean_us"] = {part: statistics.mean(s[f"{part}_pose_us"] for s in warm) for part in ("body", "face")}
            report["rebuild_retarget_cache"] = args.rebuild_retarget_cache
            assert max(s["jaw_curve"] for s in meta) > .5, "Face animation received no jaw curve"
            jaw_range = max(s["jaw_rotation_degrees"] for s in meta) - min(s["jaw_rotation_degrees"] for s in meta)
            assert jaw_range > 5, f"Facial jaw bone did not articulate: {jaw_range} degrees"
            assert max(s["wrist_z"] for s in meta) - min(s["wrist_z"] for s in meta) > 30
            assert max(s["x"] for s in meta) > 180
            assert all(s["jaw_curve"] == 0 for s in meta[-3:]), "Disconnected MetaHuman jaw stayed active"
            assert all(s[key] == 0 for s in meta[-3:] for key in ("eyeBlinkL", "browRaiseOuterL", "mouthCornerPullL", "mouthCornerDepressL")), "Disconnected facial controls stayed active"
            assert max(s["eyeBlinkL"] for s in meta) > .5, "Blink never closed"
            # Hold the mouth silent while checking independent facial expression poses.
            poses = {}
            controller = BehaviorController()
            for index, expression in enumerate(("neutral", "curious", "happy", "concerned", "neutral")):
                controller.apply({"version": 1, "id": f"face-{index}", "action": "expression",
                                  "params": {"name": expression, "intensity": 1}})
                for _ in range(40):
                    write_snapshot(snapshot, controller.snapshot())
                    controller.tick(1 / 30)
                    time.sleep(1 / 30)
                poses[expression] = read_samples(folder / "metahuman-runtime.jsonl")[-1]
            assert poses["curious"]["browRaiseOuterL"] > .6
            assert poses["happy"]["mouthCornerPullL"] > .95
            assert poses["concerned"]["mouthCornerDepressL"] > .38
            for expression in ("happy", "concerned"):
                assert math.dist(poses[expression]["FACIAL_L_LipCorner"], poses["neutral"]["FACIAL_L_LipCorner"]) > .01, "Expression did not deform lip bone"
            controller.apply({"version": 1, "id": "active-face", "action": "expression", "params": {"name": "happy", "intensity": 1}})
            for _ in range(30):
                write_snapshot(snapshot, controller.snapshot())
                controller.tick(1 / 30)
                time.sleep(1 / 30)
            assert read_samples(folder / "metahuman-runtime.jsonl")[-1]["mouthCornerPullL"] > .9
            controller.apply({"version": 1, "id": "pause-face", "action": "pause", "params": {}})
            for _ in range(15):
                write_snapshot(snapshot, controller.snapshot())
                controller.tick(1 / 30)
                time.sleep(1 / 30)
            stopped = read_samples(folder / "metahuman-runtime.jsonl")[-1]
            assert all(stopped[key] == 0 for key in ("eyeBlinkL", "browRaiseOuterL", "mouthCornerPullL", "mouthCornerDepressL"))
            controller.apply({"version": 1, "id": "resume-eyes", "action": "resume", "params": {}})
            eyes = []
            for index, y in enumerate((-500, 500)):
                controller.apply({"version": 1, "id": f"eyes-{index}", "action": "look_at",
                                  "params": {"x": 100, "y": y, "z": 160}})
                for _ in range(45):
                    write_snapshot(snapshot, controller.snapshot())
                    controller.tick(1 / 30)
                    time.sleep(1 / 30)
                eyes.append(read_samples(folder / "metahuman-runtime.jsonl")[-1])
            def angle(a, b):
                return math.degrees(2 * math.acos(min(1, abs(sum(x * y for x, y in zip(a, b))))))
            for bone in ("FACIAL_L_Eye", "FACIAL_R_Eye"):
                assert angle(eyes[0][bone], eyes[1][bone]) > 5, "Eye bone did not follow gaze"
            controller.apply({"version": 1, "id": "pause-eyes", "action": "pause", "params": {}})
            for _ in range(15):
                write_snapshot(snapshot, controller.snapshot())
                controller.tick(1 / 30)
                time.sleep(1 / 30)
            held = read_samples(folder / "metahuman-runtime.jsonl")[-3:]
            for bone in ("FACIAL_L_Eye", "FACIAL_R_Eye"):
                assert angle(held[0][bone], held[-1][bone]) < .1, "Paused eyes drifted"
            report["checks"] += ["eye_gaze_bones", "eye_pause_hold"]
            report["checks"] += ["facial_expression_bones", "blink", "facial_pause"]
            report["metahuman_jaw_range_degrees"] = jaw_range
            report["checks"] += ["metahuman_jaw_bone", "metahuman_wrist", "metahuman_movement", "metahuman_disconnect"]
            report["limits"] = "Sampled frame times; synthetic facial controls, no audio or live AI; prototype retargeting."
        (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        print(f"Evidence: {folder}")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=15)


if __name__ == "__main__":
    main()

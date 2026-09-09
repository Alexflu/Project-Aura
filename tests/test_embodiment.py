import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aura.embodiment import BehaviorController, validate_command, write_snapshot
from tools.skeleton_zero import load_timeline, replay, ROOT


def cue(action, params=None, identifier="test"):
    return {"version": 1, "id": identifier, "action": action, "params": params or {}}


class EmbodimentTests(unittest.TestCase):
    def test_invalid_commands_do_not_mutate_state(self):
        controller = BehaviorController()
        invalid = [cue("launch"), cue("gesture", {"name": "run.exe", "duration_s": 1}),
                   cue("speak", {"duration_s": True}), cue("walk_to", {"x": math.nan, "y": 0}),
                   cue("look_at", {"x": 0, "y": 0, "z": math.inf}),
                   cue("walk_to", {"x": 501, "y": 0}), cue("idle", {"extra": 1}),
                   {**cue("idle"), "version": True}, {**cue("idle"), "version": 2},
                   {**cue("idle"), "action": []}, {**cue("idle"), "id": ""}]
        before = copy.deepcopy(controller.__dict__)
        for command in invalid:
            with self.subTest(command=command), self.assertRaises(ValueError):
                controller.apply(command)
            self.assertEqual(controller.__dict__, before)

    def test_duplicate_does_not_restart_speech(self):
        controller = BehaviorController()
        command = cue("speak", {"duration_s": 1})
        controller.apply(command)
        controller.tick(.25)
        self.assertEqual(controller.apply(command), "duplicate")
        self.assertEqual(controller.speech_remaining, .75)

    def test_pause_cancels_all_channels_and_resume_does_not_replay(self):
        controller = BehaviorController()
        controller.apply(cue("walk_to", {"x": 200, "y": 0}, "move"))
        controller.apply(cue("speak", {"duration_s": 3}, "speech"))
        controller.apply(cue("gesture", {"name": "wave", "duration_s": 3}, "wave"))
        controller.tick(.2)
        controller.apply(cue("pause"))
        position = list(controller.position)
        self.assertEqual(controller.apply(cue("walk_to", {"x": 300, "y": 0}, "blocked")), "paused")
        controller.apply(cue("resume", identifier="resume"))
        controller.tick(.2)
        snapshot = controller.snapshot()
        self.assertEqual(controller.position, position)
        self.assertEqual(snapshot["mouth_open"], 0)
        self.assertEqual(snapshot["gesture"], "none")
        self.assertFalse(snapshot["moving"])

    def test_diagonal_speed_and_arrival_do_not_overshoot(self):
        controller = BehaviorController()
        controller.apply(cue("walk_to", {"x": 30, "y": 40}))
        controller.tick(.25)
        self.assertAlmostEqual(math.hypot(*controller.position), 25)
        controller.tick(.25)
        controller.tick(.25)
        self.assertEqual(controller.position, [30, 40])
        self.assertFalse(controller.snapshot()["moving"])

    def test_speech_gesture_expire_and_gaze_persists(self):
        controller = BehaviorController()
        controller.apply(cue("look_at", {"x": 100, "y": -50, "z": 160}, "gaze"))
        controller.apply(cue("speak", {"duration_s": .25}, "speech"))
        controller.apply(cue("gesture", {"name": "nod", "duration_s": .25}, "gesture"))
        self.assertGreater(controller.snapshot()["mouth_open"], 0)
        controller.tick(.25)
        snapshot = controller.snapshot()
        self.assertEqual((snapshot["mode"], snapshot["gesture"], snapshot["mouth_open"]), ("idle", "none", 0))
        self.assertEqual(controller.gaze, [100, -50, 160])

    def test_listen_interrupts_speech_and_motion(self):
        controller = BehaviorController()
        controller.apply(cue("speak", {"duration_s": 2}))
        controller.apply(cue("listen", identifier="listen"))
        self.assertEqual(controller.snapshot()["mode"], "listening")
        self.assertEqual(controller.snapshot()["mouth_open"], 0)

    def test_tick_rejects_invalid_time(self):
        for value in (-1, .5, math.inf, True):
            with self.assertRaises(ValueError):
                BehaviorController().tick(value)

    def test_atomic_failure_preserves_previous_snapshot_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            write_snapshot(path, {"sequence": 1})
            with patch("aura.embodiment.os.replace", side_effect=PermissionError), self.assertRaises(PermissionError):
                write_snapshot(path, {"sequence": 2})
            self.assertEqual(json.loads(path.read_text()), {"sequence": 1})
            self.assertEqual([p.name for p in Path(folder).iterdir()], ["state.json"])

    def test_replay_writes_all_six_behaviors_and_final_idle(self):
        timeline = load_timeline(ROOT / "examples/skeleton-zero/timeline.json")
        snapshots = []
        with patch("tools.skeleton_zero.write_snapshot", side_effect=lambda p, s: snapshots.append(s)):
            replay(timeline, "unused", fast=True)
        self.assertEqual({s["mode"] for s in snapshots}, {"idle", "listening", "speaking"})
        self.assertTrue(any(s["moving"] for s in snapshots))
        self.assertTrue(any(s["gesture"] == "wave" for s in snapshots))
        self.assertTrue(any(s["gaze_y"] == 100 for s in snapshots))
        self.assertEqual(snapshots[-1]["mode"], "idle")
        self.assertFalse(snapshots[-1]["moving"])
        self.assertEqual([s["sequence"] for s in snapshots], list(range(1, len(snapshots) + 1)))

    def test_windows_reader_lock_is_retried(self):
        import os
        replace = os.replace
        attempts = []
        def locked_once(source, target):
            attempts.append(1)
            if len(attempts) == 1:
                raise PermissionError("Reader still has the file open")
            return replace(source, target)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            with patch("aura.embodiment.os.replace", side_effect=locked_once):
                write_snapshot(path, {"sequence": 2})
            self.assertEqual(json.loads(path.read_text()), {"sequence": 2})
            self.assertEqual(len(attempts), 2)

    def test_interrupt_writes_final_idle(self):
        snapshots = []
        with patch("tools.skeleton_zero.write_snapshot", side_effect=lambda p, s: snapshots.append(s)), \
                patch("tools.skeleton_zero.time.sleep", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            replay([{"at_s": 0, "command": cue("speak", {"duration_s": 3})}], "unused")
        self.assertEqual(snapshots[-1]["mouth_open"], 0)

    def test_bad_timeline_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for value in ([], [{"at_s": -1, "command": cue("idle")}],
                          [{"at_s": 1, "command": cue("idle")}, {"at_s": 0, "command": cue("idle", identifier="b")}],
                          [{"at_s": 0, "command": cue("idle")}] * 2):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    load_timeline(path)

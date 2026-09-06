import math
from pathlib import Path
import struct
import tempfile
import unittest
import wave
from aura.voice import Clip, Speech
from aura.core import AuraError, Store
from aura.presence import dock_position


def sample(path, width=2):
    with wave.open(str(path), "wb") as out:
        out.setparams((1, width, 16000, 0, "NONE", "not compressed"))
        # Silence, audible tone, silence: enough to catch a free-running mouth.
        values = [0] * 3200 + [int(math.sin(i * .2) * 9000) for i in range(6400)] + [0] * 3200
        out.writeframes(b"".join(struct.pack("<h", v) for v in values))


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "audio.wav"
        sample(self.path)

    def test_mouth_tracks_silence_and_signal(self):
        clip = Clip.read(self.path)
        self.assertEqual(clip.level(.1), 0)
        self.assertGreater(clip.level(.3), .5)
        self.assertEqual(clip.level(.7), 0)
        self.assertEqual(clip.level(-.1), 0)
        self.assertEqual(clip.level(clip.duration), 0)

    def test_bad_format_and_truncation_rejected(self):
        sample(self.path, width=1)
        with self.assertRaises(AuraError):
            Clip.read(self.path)
        sample(self.path)
        self.path.write_bytes(self.path.read_bytes()[:-100])
        with self.assertRaises(AuraError):
            Clip.read(self.path)

    def test_stop_cancels_playback_and_removes_copy(self):
        calls = []
        speech = Speech(player=calls.append)
        self.addCleanup(speech.stop)
        speech.load(self.path)
        output = calls[0]
        self.assertTrue(output.exists())
        speech.stop()
        self.assertEqual(calls[-1], None)
        self.assertFalse(output.exists())
        self.assertTrue(self.path.exists())

    def test_completion_and_delay_use_audio_clock(self):
        now = [10.0]
        speech = Speech(clock=lambda: now[0], player=lambda p: None)
        self.addCleanup(speech.stop)
        speech.load(self.path)
        speech.delay_ms = 100
        now[0] = 10.15
        self.assertEqual(speech.poll(), 0)
        now[0] = 10.4
        self.assertGreater(speech.poll(), .5)
        now[0] = 11
        self.assertEqual(speech.poll(), 0)
        self.assertEqual(speech.state, "idle")

    def test_text_limits_checked_before_subprocess(self):
        speech = Speech(player=lambda p: None)
        for text in ("", " " * 10, "a" * 1001, None):
            with self.assertRaises(AuraError):
                speech.speak(text)
        self.assertIsNone(speech.process)

    def test_playback_failure_cleans_temp(self):
        def fail(path):
            raise RuntimeError("device failed")
        speech = Speech(player=fail)
        with self.assertRaises(AuraError):
            speech.load(self.path)
        self.assertIsNone(speech.temp)
        self.assertEqual(speech.state, "idle")


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "state.db")
        self.store.preferences([], "violet", False, True, False, False)

    def test_performance_requires_approval_and_is_not_replayed(self):
        calls = []
        payload = {"text": "$(not code) <speak>literal text</speak>", "mood": "happy"}
        request = self.store.enqueue("performance", payload)
        self.assertEqual(calls, [])
        self.store.resolve(request["request_id"], True, lambda _: None, lambda p: calls.append(p) or "started")
        self.assertEqual(calls, [payload])
        with self.assertRaises(AuraError):
            self.store.resolve(request["request_id"], True, lambda _: None, calls.append)
        self.assertEqual(len(calls), 1)

    def test_reject_and_pause_never_speak(self):
        for paused in (False, True):
            request = self.store.enqueue("performance", {"text": "hello", "mood": "neutral"})
            if paused:
                self.store.set_paused(True)
                with self.assertRaises(AuraError):
                    self.store.resolve(request["request_id"], True, lambda _: None, lambda _: self.fail())
            else:
                self.store.resolve(request["request_id"], False, lambda _: None, lambda _: self.fail())

    def test_invalid_performance_rejected(self):
        for payload in ({"text": "x", "mood": "arbitrary"}, {"text": "x" * 1001, "mood": "happy"},
                        {"text": "x", "mood": "happy", "command": "bad"}):
            with self.assertRaises(AuraError):
                self.store.enqueue("performance", payload)

    def test_docking_respects_negative_monitor_and_taskbar(self):
        self.assertEqual(dock_position((-1920, 0, 0, 1040), 250, 340, "right"), (-262, 688, 250, 340))
        self.assertEqual(dock_position((0, 0, 100, 100), 250, 340, "left"), (0, 0, 100, 100))

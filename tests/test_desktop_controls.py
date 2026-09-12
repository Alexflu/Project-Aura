from pathlib import Path
from types import SimpleNamespace
import json
import os
import tempfile
import time
import unittest
from aura.embodied_speech import EmbodiedSpeech
from tools.unreal_desktop import DesktopControls


class Player:
    state = "idle"
    calls = 0
    def speak(self, text):
        self.calls += 1
        self.state = "preparing"
    def stop(self):
        self.state = "idle"
    def poll(self):
        return .5 if self.state == "playing" else 0


class Process:
    code = None
    def poll(self):
        return self.code
    def terminate(self):
        self.code = -1
    def wait(self, timeout):
        return self.code


class DesktopControlTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.player = Player()
        c = self.controls = DesktopControls.__new__(DesktopControls)
        c.folder = Path(temp.name)
        c.bridge = EmbodiedSpeech(self.player)
        c.process = Process()
        c.closed = c.ready = False
        c.started = time.monotonic()
        c.ready_since = time.time()
        c.last_error = ""
        c.smoke_seconds = 0
        self.destroyed = False
        c.root = SimpleNamespace(after=lambda *args: None, destroy=self.destroy)
        c.entry = SimpleNamespace(get=lambda: "Hello")
        c.speak_button = c.pause_button = SimpleNamespace(configure=lambda **kw: None)
        self.message = ""
        c.status = SimpleNamespace(set=self.set_message)

    def destroy(self):
        self.destroyed = True

    def set_message(self, text):
        self.message = text

    def test_speech_requires_ready_unpaused_renderer(self):
        c = self.controls
        c.speak()
        c.ready = True
        c.bridge.pause()
        c.speak()
        self.assertEqual(self.player.calls, 0)
        c.pause()
        c.speak()
        self.assertEqual(self.player.calls, 1)

    def test_renderer_exit_stops_audio_and_closes_controls(self):
        c = self.controls
        self.player.state = "playing"
        c.process.code = 0
        c.tick()
        self.assertTrue(self.destroyed)
        self.assertEqual(self.player.state, "idle")
        snapshot = json.loads((c.folder / "behavior.json").read_text())
        self.assertEqual(snapshot["mouth_open"], 0)
        c.close()  # Closing again must be harmless.

    def test_stale_renderer_stops_playback_and_disables_restart(self):
        c = self.controls
        c.ready = True
        self.player.state = "playing"
        status = c.folder / "desktop-status.json"
        status.write_text("{}")
        os.utime(status, (time.time() - 10, time.time() - 10))
        c.tick()
        self.assertEqual(c.process.code, -1)
        self.assertEqual(self.player.state, "idle")
        self.assertFalse(c.ready)
        self.assertIn("stopped responding", self.message)
        c.speak()
        self.assertEqual(self.player.calls, 0)

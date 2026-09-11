import unittest
from aura.embodied_speech import EmbodiedSpeech


class Player:
    state = "idle"
    level = 0
    def speak(self, text):
        self.state = "preparing"
    def stop(self):
        self.state = "idle"
    def poll(self):
        return self.level


class EmbodiedSpeechTests(unittest.TestCase):
    def test_playback_envelope_and_silence_replace_synthetic_cue(self):
        player = Player()
        bridge = EmbodiedSpeech(player)
        bridge.speak("Hello")
        self.assertEqual(bridge.snapshot(.03)["mouth_open"], 0)
        player.state, player.level = "playing", .72
        snapshot = bridge.snapshot(.03)
        self.assertEqual(snapshot["mode"], "speaking")
        self.assertEqual(snapshot["mouth_open"], .72)
        player.level = 0
        self.assertEqual(bridge.snapshot(.03)["mouth_open"], 0)
        player.state = "idle"
        self.assertEqual(bridge.snapshot(.03)["mode"], "idle")

    def test_pause_stops_audio_and_cannot_restart(self):
        player = Player()
        bridge = EmbodiedSpeech(player)
        player.state, player.level = "playing", 1
        bridge.pause()
        bridge.speak("Must remain paused")
        self.assertEqual(player.state, "idle")
        self.assertEqual(bridge.snapshot(.03)["mouth_open"], 0)

    def test_player_error_stops_playback(self):
        player = Player()
        bridge = EmbodiedSpeech(player)
        def fail():
            raise RuntimeError("Device unavailable")
        player.poll = fail
        player.state = "playing"
        with self.assertRaises(RuntimeError):
            bridge.snapshot(.03)
        self.assertEqual(player.state, "idle")

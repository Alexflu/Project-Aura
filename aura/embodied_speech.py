"""Local playback adapter for the existing behavior snapshot protocol."""
from .embodiment import BehaviorController
from .voice import Speech


class EmbodiedSpeech:
    def __init__(self, speech=None):
        if speech is None:
            from .playback_clock import WavePlayer
            player = WavePlayer()
            speech = Speech(player=player, playback_position=player.position)
        self.speech = speech
        self.behavior = BehaviorController()

    def speak(self, text):
        if not self.behavior.paused:
            self.speech.speak(text)

    def stop(self):
        self.speech.stop()
        self.behavior.stop()

    def pause(self):
        self.stop()
        self.behavior.paused = True

    def snapshot(self, dt):
        if self.behavior.paused:
            self.speech.stop()
        self.behavior.tick(dt)
        try:
            level = self.speech.poll()
        except Exception:
            self.stop()
            raise
        result = self.behavior.snapshot()
        # Playback owns speech timing; never use the offline sine-wave cue here.
        playing = self.speech.state == "playing" and not self.behavior.paused
        result["mode"] = "speaking" if playing else "idle"
        result["mouth_open"] = level if playing else 0.0
        return result

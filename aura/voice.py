"""Local Windows speech and bounded PCM playback, with an audio envelope.

No microphone, network, account access, or background recording. User text is
JSON data on stdin to a fixed script, never executable shell or SSML input.
"""
from array import array
from dataclasses import dataclass
import base64
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave
from .core import AuraError

MAX_SECONDS = 120
MAX_BYTES = 24 * 1024 * 1024
STEP = .02
MOODS = ("neutral", "happy", "thoughtful", "focused", "sleepy")


@dataclass(frozen=True)
class Clip:
    data: bytes
    levels: tuple
    duration: float

    @classmethod
    def read(cls, path):
        with Path(path).open("rb") as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise AuraError("Choose a WAV smaller than 24 MB and shorter than two minutes.")
        try:
            with wave.open(io.BytesIO(data), "rb") as wav:
                rate, channels, count = wav.getframerate(), wav.getnchannels(), wav.getnframes()
                if (wav.getsampwidth() != 2 or channels not in (1, 2) or
                        not 8000 <= rate <= 48000 or count <= 0 or count / rate > MAX_SECONDS):
                    raise AuraError("Use 16-bit PCM WAV, mono/stereo, 8–48 kHz, up to two minutes.")
                raw = wav.readframes(count)
                if len(raw) != count * channels * 2:
                    raise AuraError("This WAV is incomplete.")
        except (wave.Error, EOFError) as exc:
            raise AuraError("This file is not a supported PCM WAV.") from exc
        samples = array("h", raw)
        if sys.byteorder != "little":
            samples.byteswap()
        block = max(1, round(rate * STEP)) * channels
        levels = []
        for start in range(0, len(samples), block):
            chunk = samples[start:start + block]
            rms = math.sqrt(sum(v * v for v in chunk) / len(chunk)) / 32768
            levels.append(rms)
        peak = max(levels, default=0)
        # Preserve actual silence; normalize for quieter installed voices.
        ceiling = max(.025, peak * .65)
        levels = tuple(0 if v < .003 else min(1, v / ceiling) for v in levels)
        return cls(data, levels, count / rate)

    def level(self, elapsed):
        if elapsed < 0 or elapsed >= self.duration:
            return 0
        return self.levels[min(len(self.levels) - 1, int(elapsed / STEP))]


SCRIPT = r'''
$ErrorActionPreference = 'Stop'
$request = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    if ($request.voice -eq 'female') {
        $speaker.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female)
    } elseif ($request.voice -eq 'male') {
        $speaker.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male)
    }
    $speaker.Rate = [int]$request.rate
    $speaker.Volume = [int]$request.volume
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $speaker.SetOutputToWaveFile([string]$request.output, $format)
    $speaker.Speak([string]$request.text)
} finally { $speaker.Dispose() }
'''


class Speech:
    def __init__(self, clock=time.monotonic, player=None):
        self.clock = clock
        self.player = player
        self.temp = None
        self.process = None
        self.clip = None
        self.state = "idle"
        self.started = 0
        self.delay_ms = 0

    def _play(self, path):
        if self.player is not None:
            self.player(path)
        else:
            import winsound
            winsound.PlaySound(str(path) if path else None,
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT if path else 0)

    def stop(self):
        if self.process:
            self.process.kill()
            self.process.wait(timeout=5)
            self.process = None
        if self.state == "playing":
            self._play(None)
        self.state, self.clip = "idle", None
        if self.temp:
            self.temp.cleanup()
            self.temp = None

    def speak(self, text, voice="default", rate=0, volume=70):
        if not isinstance(text, str) or not text.strip() or len(text) > 1000:
            raise AuraError("Enter between 1 and 1,000 characters to speak.")
        if voice not in ("default", "female", "male") or type(rate) is not int or not -5 <= rate <= 5 or type(volume) is not int or not 0 <= volume <= 100:
            raise AuraError("Unsupported voice settings.")
        if os.name != "nt":
            raise AuraError("Local speech currently requires Windows.")
        self.stop()
        self.temp = tempfile.TemporaryDirectory(prefix="aura-speech-")
        self.output = Path(self.temp.name) / "speech.wav"
        # Resolve Windows' installed PowerShell, not an executable from PATH.
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        if not ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer)):
            self.stop()
            raise AuraError("Windows speech could not be located.")
        exe = Path(buffer.value) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        command = base64.b64encode(SCRIPT.encode("utf-16le")).decode("ascii")
        try:
            self.process = subprocess.Popen([str(exe), "-NoProfile", "-NonInteractive", "-EncodedCommand", command],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            request = dict(text=text, voice=voice, rate=rate, volume=volume, output=str(self.output))
            self.process.stdin.write(json.dumps(request, ensure_ascii=True).encode("ascii"))
            self.process.stdin.close()
            self.state, self.started = "preparing", self.clock()
        except (OSError, ValueError):
            self.stop()
            raise AuraError("Windows speech could not start. Try an installed default voice.")

    def load(self, path):
        clip = Clip.read(path)
        self.stop()
        self.temp = tempfile.TemporaryDirectory(prefix="aura-audio-")
        self.output = Path(self.temp.name) / "playback.wav"
        self.output.write_bytes(clip.data)
        self._begin(clip)

    def _begin(self, clip):
        try:
            self._play(self.output)
        except (OSError, RuntimeError):
            self.stop()
            raise AuraError("Windows could not play this audio.")
        self.clip, self.started, self.state = clip, self.clock(), "playing"

    def poll(self):
        if self.state == "preparing":
            code = self.process.poll()
            if code is None:
                if self.clock() - self.started > 60:
                    self.stop()
                    raise AuraError("Speech preparation timed out. Try shorter text or the default voice.")
                return 0
            self.process = None
            if code != 0:
                self.stop()
                raise AuraError("Windows speech failed. Try the default voice or play a WAV instead.")
            try:
                self._begin(Clip.read(self.output))
            except (AuraError, OSError):
                self.stop()
                raise
        if self.state == "playing":
            elapsed = self.clock() - self.started
            if elapsed >= self.clip.duration + max(0, self.delay_ms / 1000):
                self.stop()
                return 0
            return self.clip.level(elapsed - self.delay_ms / 1000)
        return 0

"""Windows WAV playback with the player's reported position (seconds)."""
import ctypes
import os
from pathlib import Path
import uuid


class WavePlayer:
    def __init__(self):
        if os.name != "nt":
            raise OSError("Windows WAV playback is required")
        self.api = ctypes.WinDLL("winmm")
        self.api.mciSendStringW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        self.api.mciSendStringW.restype = ctypes.c_uint
        self.alias = "aura" + uuid.uuid4().hex
        self.opened = False

    def command(self, command):
        result = ctypes.create_unicode_buffer(256)
        error = self.api.mciSendStringW(command, result, len(result), None)
        if error:
            raise OSError(f"Windows playback command failed ({error})")
        return result.value

    def __call__(self, path):
        if self.opened:
            self.command(f"close {self.alias}")
            self.opened = False
        if path is None:
            return
        path = str(Path(path).resolve())
        if any(char in path for char in ('"', '\n', '\r')):
            raise ValueError("Invalid playback path")
        self.command(f'open "{path}" type waveaudio alias {self.alias}')
        self.opened = True
        try:
            self.command(f"set {self.alias} time format milliseconds")
            self.command(f"play {self.alias}")
        except Exception:
            self(None)
            raise

    def position(self):
        if not self.opened or self.command(f"status {self.alias} mode") != "playing":
            return None
        return int(self.command(f"status {self.alias} position")) / 1000

"""Launch packaged desktop in an isolated profile, capture only its window, then close it."""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("exe", type=Path)
parser.add_argument("--screenshot", type=Path)
args = parser.parse_args()
user32 = ctypes.windll.user32
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
with tempfile.TemporaryDirectory() as temp:
    proc = subprocess.Popen([str(args.exe.resolve()), "--data", str(Path(temp) / "state.db")])
    windows = []
    @callback_type
    def callback(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == proc.pid and user32.IsWindowVisible(hwnd):
            windows.append(hwnd)
        return True
    try:
        for _ in range(40):
            user32.EnumWindows(callback, 0)
            if windows or proc.poll() is not None:
                break
            time.sleep(0.25)
        assert windows, "Packaged desktop did not open a visible window"
        time.sleep(0.5)
        if args.screenshot:
            from PIL import ImageGrab
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            ImageGrab.grab(window=windows[0]).save(args.screenshot)
        for hwnd in windows:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)
        assert proc.wait(timeout=10) == 0, "Packaged application did not close cleanly"
        assert (Path(temp) / "state.db").exists()
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
print("Packaged desktop smoke passed: visible window, state initialized, clean shutdown.")

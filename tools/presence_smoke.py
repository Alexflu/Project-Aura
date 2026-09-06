"""Own-window checks with temporary state and silent audio backend."""
from pathlib import Path
import ctypes
import sys
import tempfile
import tkinter as tk
import wave
import struct
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from aura.ui import App, prepare_display

from aura.core import Store
from aura.voice import Speech

with tempfile.TemporaryDirectory() as temp:
    prepare_display()
    root = tk.Tk()
    app = App(root, Store(Path(temp) / "state.db"))
    calls = []
    app.speech = Speech(player=calls.append)
    app.approved_look()
    app.apply_preview()
    app.tabs.select(app.presence_page)
    path = Path(temp) / "tone.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        wav.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(i * .2))) for i in range(16000)))
    app.speech.load(path)
    root.after(160, root.quit)
    root.mainloop()
    assert app.avatar.audio_level is not None and app.avatar.audio_level > .16
    app.pause()
    assert app.speech.state == "idle" and calls[-1] is None
    app.pause()
    app.dock_avatar("right")
    assert app.floating.winfo_exists()
    app.mood.set("happy")
    app.effect.set("hologram")
    app.apply_presence()
    app.entrance()
    root.after(180, root.quit)
    root.mainloop()
    assert app.float_avatar.mood == "happy" and app.float_avatar.effect == "hologram"
    app.floating.withdraw()
    root.lift()
    root.update_idletasks()
    out = Path(__file__).resolve().parents[1] / "artifacts/screenshots-v3"
    out.mkdir(parents=True, exist_ok=True)
    hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2)
    ImageGrab.grab(window=hwnd).save(out / "presence.png")
    app.close()
print("Presence smoke passed: audio level, pause cancels, docking, mood/effect, entrance, close.")

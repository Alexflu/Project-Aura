"""UI labels, floating cutout controls, rendering and short timing sample."""
from pathlib import Path
import ctypes
import sys
import tempfile
import time
import tkinter as tk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from aura.ui import App, prepare_display
from aura.core import Store

with tempfile.TemporaryDirectory() as temp:
    prepare_display()
    root = tk.Tk()
    app = App(root, Store(Path(temp) / "state.db"))
    app.approved_look()
    app.apply_preview()
    root.after(600, root.quit)
    root.mainloop()
    assert app.look_boxes["outfit"].get() == "Tactical Ops"
    app.look_boxes["outfit"].display.set("Stealth Striker")
    app.preview_controls()
    app.apply_preview()
    assert app.store.read()["look"]["outfit"] == "stealth"
    assert not app.look_boxes["accessory"].winfo_ismapped()
    app.toggle_float()
    root.update_idletasks()
    assert app.floating.overrideredirect()
    assert app.float_avatar.desktop_mode
    old = app.floating.winfo_height()
    app.resize_float(1.1)
    root.update_idletasks()
    assert app.floating.winfo_height() > old
    app.dock_avatar("right")
    root.after(200, root.quit)
    root.mainloop()
    app.toggle_float()
    # Record actual callback spacing after cache warmup, without a hardware-dependent assertion.
    intervals = []
    previous = [time.monotonic()]
    original = app.avatar.animate
    def measured():
        now = time.monotonic()
        intervals.append(now - previous[0])
        previous[0] = now
        original()
    app.avatar.animate = measured
    root.after(1800, root.quit)
    root.mainloop()
    out = Path(__file__).resolve().parents[1] / "artifacts/screenshots-v4"
    out.mkdir(parents=True, exist_ok=True)
    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2)
    ImageGrab.grab(window=hwnd).save(out / "studio.png")
    if intervals:
        print("Observed callback rate:", round(len(intervals) / sum(intervals), 1), "fps")
    app.close()
print("Refinement smoke passed: label mapping, save, hidden unavailable controls, frameless floating, resize, docking.")

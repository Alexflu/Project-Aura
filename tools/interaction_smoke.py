"""Regression: float and mouth preview from Appearance before visiting Presence."""
import ctypes
from pathlib import Path
import sys
import tempfile
import tkinter as tk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from aura.core import Store
from aura.ui import App, prepare_display

with tempfile.TemporaryDirectory() as temp:
    store = Store(Path(temp) / "state.db")
    store.apply(dict(store.read()["look"], outfit="stealth", hair="pixie"))
    prepare_display()
    root = tk.Tk()
    app = App(root, store)
    assert app.tabs.select() == str(app.look_page)
    app.toggle_float()
    root.after(700, root.quit)
    root.mainloop()
    assert app.floating.winfo_viewable()
    assert app.float_avatar.find_withtag("body")
    app.demo_speaking()
    opened = []
    def observe():
        opened.append(app.float_avatar.motion.mouth)
        if len(opened) < 15:
            root.after(70, observe)
        else:
            root.quit()
    observe()
    root.mainloop()
    assert max(opened) > .3, opened
    assert app.avatar.expression == app.float_avatar.expression == "speaking"
    assert app.mouth_preview_btn.cget("text") == "Stop mouth preview"
    app.end_demo()
    assert app.avatar.expression == app.float_avatar.expression == "idle"
    app.control_wheel.stop()
    app.control_wheel.show()
    assert len(app.float_avatar.find_withtag("wheel")) == 12
    out = Path("artifacts/screenshots-v5")
    out.mkdir(parents=True, exist_ok=True)
    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetAncestor(app.floating.winfo_id(), 2)
    ImageGrab.grab(window=hwnd).save(out / "wheel.png")
    app.control_wheel.hide()
    assert not app.float_avatar.find_withtag("wheel")
    app.toggle_float()
    app.toggle_float()
    root.after(200, root.quit)
    root.mainloop()
    assert app.floating.winfo_viewable()
    app.close()
print("Interaction smoke passed: float from Appearance, visible mouth preview on both surfaces, wheel show/hide, reopen.")

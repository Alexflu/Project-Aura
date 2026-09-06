"""Exercise illustrated controls and capture this test window only."""
from pathlib import Path
import sys
import tempfile
import tkinter as tk
import ctypes
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
    root.update_idletasks()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "screenshots-v2"
    out.mkdir(parents=True, exist_ok=True)
    for outfit in ("tactical", "stealth"):
        for hair in ("pixie", "long"):
            app.look_vars["outfit"].set(outfit)
            app.look_vars["hair"].set(hair)
            app.preview_controls()
            app.apply_preview()
            for mode in ("idle", "speaking"):
                app.avatar.expression = mode
                app.avatar.tick = 20
                root.after(180, root.quit)
                root.mainloop()
                from aura.illustrated import draw
                app.avatar.tick = 18
                draw(app.avatar)
                root.update_idletasks()
                assert hasattr(app.avatar, "sprite_photo")
                assert str(app.look_boxes["accessory"].cget("state")) == "disabled"
                hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2)
                ImageGrab.grab(window=hwnd).save(out / f"{outfit}-{hair}-{mode}.png")
    app.toggle_float()
    root.update_idletasks()
    app.pause()
    tick = app.avatar.tick
    root.after(180, root.quit)
    root.mainloop()
    assert app.avatar.tick == tick
    app.pause()
    app.reduced.set(True)
    app.save_preferences()
    assert app.avatar.reduced and app.float_avatar.reduced
    app.close()
print("Illustrated smoke passed: four looks, expressions, floating, pause, reduced motion.")


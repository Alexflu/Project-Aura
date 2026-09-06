"""Exercise the actual desktop widgets using temporary data. Optional own-window screenshots."""
import argparse
import sys
from pathlib import Path
import tempfile
import tkinter as tk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.core import Store
from aura.ui import App, prepare_display

parser = argparse.ArgumentParser()
parser.add_argument("--screenshots", type=Path)
args = parser.parse_args()
with tempfile.TemporaryDirectory() as temp:
    prepare_display()
    root = tk.Tk()
    app = App(root, Store(Path(temp) / "aura.db"))
    root.update_idletasks()
    app.preview_request()
    assert app.store.read()["look"]["hair"] == "long"
    app.apply_preview()
    assert app.store.read()["look"]["hair"] == "bob"
    app.undo()
    app.interest_vars["making"].set(True)
    app.favorite.set("violet")
    app.save_preferences()
    app.suggest()
    assert app.preview["outfit"] == "engineer"
    app.apply_preview()
    app.activity.set("making")
    app.record()
    app.toggle_float()
    root.update_idletasks()
    assert app.floating.winfo_exists()
    app.toggle_float()
    app.pause()
    assert app.store.read()["paused"]
    app.pause()
    if args.screenshots:
        from PIL import ImageGrab
        args.screenshots.mkdir(parents=True, exist_ok=True)
        root.lift()
        root.attributes("-topmost", True)
        for page, name in ((app.look_page, "appearance"), (app.prefs_page, "interests"), (app.connect_page, "connection"), (app.data_page, "data")):
            app.tabs.select(page)
            root.update_idletasks()
            root.after(300, root.quit)
            root.mainloop()
            import ctypes
            hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2)
            ImageGrab.grab(window=hwnd).save(args.screenshots / (name + ".png"))
    app.close()
print("GUI smoke passed: preview, apply, undo, preferences, suggestion, activity, floating avatar, pause.")

"""Actual tray show/hide/recovery and articulated model, isolated from user data."""
from pathlib import Path
import sys,tempfile,tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.ui import App,prepare_display
from aura.core import Store
from aura.tray import Tray,Instance,Preferences
from PIL import ImageGrab
import ctypes

def wait(root,ms=300):root.after(ms,root.quit);root.mainloop()

with tempfile.TemporaryDirectory() as temp:
    prepare_display();root=tk.Tk();app=App(root,Store(Path(temp)/'state.db'))
    errors=[];root.report_callback_exception=lambda typ,exc,tb:errors.append(str(exc))
    app.instance=Instance(app.store.path);app.tray=Tray();app.lifecycle_poll()
    app.toggle_float();wait(root,600)
    assert app.tray.visible
    app.hide_studio();assert root.state()=='withdrawn'
    app.set_tray_visible();wait(root)
    assert not app.tray.visible and app.floating.winfo_viewable()
    app.set_tray_visible();wait(root);assert app.tray.visible
    second=Instance(app.store.path);assert not second.primary;second.close()
    wait(root);assert root.state()=='normal'
    app.use_reference_model();app.inventory.equip('aura.dagger');app.refresh_equipment();app.perform({'cue':'draw'})
    app.tabs.select(app.model_page);wait(root,850)
    assert app.avatar.model and app.float_avatar.model
    out=Path('artifacts/screenshots-v7');out.mkdir(parents=True,exist_ok=True)
    ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)).save(out/'rig-studio.png')
    app.hide_studio();app.set_tray_visible();wait(root)
    app.toggle_float();wait(root);assert root.state()=='normal' # Never silently orphan controls.
    app.tabs.select(app.presence_page);wait(root)
    ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)).save(out/'presence.png')
    app.hide_studio();app.store.preferences([], 'violet', False, True, False, False)
    app.store.enqueue('appearance', {'palette':'ocean'})
    app.refresh_requests();wait(root)
    assert root.state()=='normal' and app.tabs.select()==str(app.connect_page)
    assert not errors,errors
    app.close()
print('Tray/rig passed: hide, restore, relaunch recovery, no taskbar Studio, rig draw, safe last-surface recovery, cleanup.')

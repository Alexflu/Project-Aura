"""Exercise release controls without Shift or user profile access."""
import ctypes
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from aura.core import Store
from aura.ui import App, prepare_display

def wait(root,ms=180):
    root.after(ms,root.quit);root.mainloop()

with tempfile.TemporaryDirectory() as temp:
    prepare_display();root=tk.Tk()
    store=Store(Path(temp)/'state.db')
    store.apply(dict(store.read()['look'],outfit='stealth',hair='pixie'))
    app=App(root,store)
    errors=[]
    root.report_callback_exception=lambda typ,exc,tb:errors.append(repr(exc))
    app.toggle_float();wait(root,350)
    # Actual Tk button invocation, then multiple paint cycles; no key state involved.
    app.float_handle.invoke();wait(root,300)
    assert app.control_wheel.pinned
    assert len(app.float_avatar.find_withtag('wheel'))==12
    app.float_handle.invoke();wait(root)
    assert not app.float_avatar.find_withtag('wheel')
    # Wheel remains visible even when the classic renderer clears its stage.
    app.float_avatar.look['outfit']='explorer'
    app.control_wheel.toggle();wait(root,200)
    assert app.float_avatar.find_withtag('wheel')
    app.control_wheel.toggle()
    app.sync_look()
    for item_id in ('aura.dagger','aura.bag','aura.crystal','aura.lightning'):
        app.inventory.equip(item_id)
    app.refresh_equipment();app.reveal_equipment();app.cast_spell();wait(root,350)
    for _ in range(12):
        if app.float_avatar.item_reveal>.5:break
        wait(root,150)
    assert app.float_avatar.item_reveal>.5
    before=store.read()
    app.open_showcase();wait(root,300)
    tour=app.showcase
    tour.toggle_pause();elapsed=tour.elapsed;wait(root,220)
    assert tour.elapsed==elapsed
    tour.elapsed=34;wait(root,200)
    assert store.read()==before
    out=Path('artifacts/screenshots-v6');out.mkdir(parents=True,exist_ok=True)
    root.update_idletasks()
    ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(tour.window.winfo_id(),2)).save(out/'tour-window.png')
    tour.close();assert tour.job is None
    app.tabs.select(app.gear_page);root.deiconify();root.lift();wait(root,500)
    assert app.tabs.select()==str(app.gear_page)
    assert app.gear_list.winfo_viewable()
    ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)).save(out/'equipment-window.png')
    app.pause();assert app.store.read()['paused']
    assert not app.showcase.window.winfo_exists()
    app.pause()
    assert not errors,errors
    app.close()
print('Release UI passed: button access, persistent wheel, equipment, effects, tutorial pause, close, unchanged profile, no callback errors.')

"""Exercise long source names, explicit follow and stop with an isolated UI profile."""
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.ui import App, prepare_display
from aura.core import Store

prepare_display()
with tempfile.TemporaryDirectory() as temp:
    root=tk.Tk();app=App(root,Store(Path(temp)/'state.db'))
    errors=[];root.report_callback_exception=lambda typ,exc,tb:errors.append(str(exc))
    try:
        label='Voicemeeter virtual recording route · A deliberately long device name that must remain readable'
        source=object();meter=Mock(name='meter');meter.name=label;meter.level.return_value=.2
        with patch('aura.app_audio.devices',return_value=[(label,source,None)]) as listing, \
             patch('aura.app_audio.DeviceMeter',return_value=meter) as factory:
            app.audio_kind.set('Input devices');app.refresh_audio_apps()
            listing.assert_called_with(1)
            app.audio_apps.selection_set(0);app.describe_audio_source()
            assert label in app.audio_details.cget('text')
            assert app.app_meter is None
            app.follow_audio_app();factory.assert_called_once_with(source)
            assert app.app_meter is meter
            app.stop_speech();assert app.app_meter is None
            app.audio_kind.set('Output devices');app.refresh_audio_apps();listing.assert_called_with(0)
            assert not app.audio_apps.curselection()
            app.audio_apps.selection_set(0);app.describe_audio_source()
            app.tabs.select(app.presence_page)
            root.update_idletasks()
            viewport=app.audio_apps.master.master.master
            viewport.yview_moveto(.7)
            root.lift();root.after(1000,root.quit);root.mainloop()
            assert not errors,errors
            from PIL import ImageGrab
            import ctypes
            out=Path('artifacts/audio-sources.png');out.parent.mkdir(exist_ok=True)
            ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(root.winfo_id(),2)).save(out)
    finally:
        app.close()
print('Audio source UI passed: long labels, input/output selection, explicit follow, stop and no implicit follow.')

"""Exercise model selection, restart and damaged-pack recovery in real Tk windows."""
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.core import Store
from aura.model_library import REFERENCE
from aura.ui import App, prepare_display


def wait(root):
    root.after(250, root.quit)
    root.mainloop()


prepare_display()
with tempfile.TemporaryDirectory() as temp:
    profile = Path(temp) / 'state.db'
    root = tk.Tk()
    app = App(root, Store(profile))
    with patch('aura.ui.filedialog.askopenfilename', return_value=str(REFERENCE)):
        app.import_model()
    key = app.model_library.selected
    app.tabs.select(app.model_page)
    app.toggle_float()
    wait(root)
    assert app.avatar.model and app.float_avatar.model
    assert len(app.model_entries) == 3
    app.close()

    root = tk.Tk()
    app = App(root, Store(profile))
    app.toggle_float()
    wait(root)
    assert app.model_library.selected == key
    assert app.avatar.model and app.float_avatar.model
    app.play_model_motion('wave')
    app.clear_model()
    assert app.model is None and app.avatar.model_motion == 'idle'
    app.model_list.selection_clear(0, tk.END)
    app.model_list.selection_set(2)
    app.choose_library_model()
    assert app.model_library.selected == key
    manifest = app.model_library.path_for(key)
    app.close()

    manifest.write_text('{}')
    root = tk.Tk()
    app = App(root, Store(profile))
    wait(root)
    assert app.model is None and 'missing or invalid' in app.status.get()
    assert manifest.exists()
    app.close()
print('Model library UI passed: import, floating render, restart, default, reselect, damaged-pack recovery.')

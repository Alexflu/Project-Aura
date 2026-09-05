"""AuraBridge: a deliberately narrow, user-approved Windows capability."""
import ctypes
import os
import subprocess
from pathlib import Path
from .core import AuraError


def launch(app):
    if app != "notepad":
        raise AuraError("This beta only supports Notepad.")
    if os.name != "nt":
        raise AuraError("Application launching is available on Windows only.")
    buffer = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer)):
        raise AuraError("Windows directory could not be located.")
    target = Path(buffer.value) / "System32" / "notepad.exe"
    if not target.is_file():
        raise AuraError("Notepad is not installed at the supported Windows location.")
    subprocess.Popen([str(target)], shell=False, close_fds=True)
    return "Launch submitted to Windows. This does not verify the window opened or edit any document."

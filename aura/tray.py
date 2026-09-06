"""Tray lifecycle and per-profile relaunch recovery. Tk runs only on its own thread."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import queue
from PIL import Image, ImageDraw


class Instance:
    """A second launch signals the existing profile instead of creating a duplicate."""
    def __init__(self, path):
        self.primary=True;self.mutex=None;self.event=None
        if os.name!='nt':return
        from ctypes import wintypes
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
        self.api.CreateMutexW.restype=wintypes.HANDLE
        self.api.CreateEventW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.BOOL,wintypes.LPCWSTR]
        self.api.CreateEventW.restype=wintypes.HANDLE
        self.api.SetEvent.argtypes=[wintypes.HANDLE]
        self.api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        key=hashlib.sha256(str(Path(path).resolve()).lower().encode()).hexdigest()[:24]
        self.mutex=self.api.CreateMutexW(None,False,'Local\\ProjectAura-'+key)
        if not self.mutex:raise OSError('Aura instance guard could not start.')
        self.primary=ctypes.get_last_error()!=183
        self.event=self.api.CreateEventW(None,False,False,'Local\\ProjectAura-recover-'+key)
        if not self.event:
            self.close();raise OSError('Aura recovery event could not start.')
        if not self.primary:self.api.SetEvent(self.event)

    def requested(self):
        return bool(self.event and self.api.WaitForSingleObject(self.event,0)==0)

    def close(self):
        for handle in (self.event,self.mutex):
            if handle:self.api.CloseHandle(handle)
        self.event=self.mutex=None


def icon_image():
    im=Image.new('RGBA',(64,64))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((2,2,62,62),radius=17,fill='#191E35',outline='#B6A0FF',width=3)
    d.polygon([(32,10),(53,50),(42,50),(32,28),(22,50),(11,50)],fill='#B6A0FF')
    d.ellipse((27,39,37,49),fill='#85E9F1')
    return im


class Tray:
    def __init__(self, visible=True):
        import pystray
        self.commands=queue.SimpleQueue()
        self.desired=bool(visible)
        def send(name):return lambda icon,item:self.commands.put(name)
        self.icon=pystray.Icon('ProjectAura',icon_image(),'Project Aura',pystray.Menu(
            pystray.MenuItem('Open Studio',send('studio'),default=True),
            pystray.MenuItem('Show / hide Aura',send('float')),
            pystray.MenuItem('Pause / resume',send('pause')),
            pystray.MenuItem('Hide tray icon',send('tray')),
            pystray.MenuItem('Quit Aura',send('quit'))))
        self.icon.run_detached(setup=lambda icon:setattr(icon,"visible",self.desired))

    @property
    def visible(self):return self.icon.visible

    @visible.setter
    def visible(self,value):
        self.desired=bool(value)
        self.icon.visible=self.desired

    def close(self):self.icon.stop()


class Preferences:
    def __init__(self,path):
        self.path=Path(path);self.tray_visible=True
        if self.path.exists():
            try:
                if self.path.stat().st_size>1024:raise ValueError()
                data=json.loads(self.path.read_text(encoding='utf-8'))
                if set(data)!={'tray_visible'} or type(data['tray_visible']) is not bool:raise ValueError()
                self.tray_visible=data['tray_visible']
            except (ValueError,TypeError):
                # Keep an invalid file for recovery; fall back to visible controls.
                self.tray_visible=True

    def save(self,visible):
        temp=self.path.with_suffix('.tmp')
        temp.write_text(json.dumps({'tray_visible':bool(visible)}),encoding='utf-8')
        temp.replace(self.path);self.tray_visible=bool(visible)

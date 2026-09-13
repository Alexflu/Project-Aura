import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import sys, json, time, tkinter as tk
from pathlib import Path
import win32gui, win32api, win32con, win32process
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.unreal_desktop import DesktopControls
from tools.unreal_body import installed_engine
root = tk.Tk()
controls = DesktopControls(root, installed_engine())
started = time.monotonic()
errors = []
state = {'phase': 'loading'}

def step():
    try:
        if time.monotonic() - started > 200:
            raise RuntimeError('Desktop check timed out')
        if state['phase'] == 'loading' and controls.ready:
            ready = json.loads((controls.folder/'desktop-ready.json').read_text())
            assert ready['opaque_pixels'] > 100 and ready['clear_pixels'] > 480*720/2
            windows=[]
            win32gui.EnumWindows(lambda h,_: windows.append(h) if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1]==controls.process.pid else None,None)
            assert len(windows)==1, windows
            h=windows[0]
            assert win32gui.GetClassName(h)=='AuraDesktopOverlay'
            style=win32gui.GetWindowLong(h,win32con.GWL_EXSTYLE)
            assert style & win32con.WS_EX_LAYERED and style & win32con.WS_EX_TOPMOST
            rect=win32gui.GetWindowRect(h)
            x,y=(rect[0]+rect[2])//2,(rect[1]+rect[3])//2
            assert win32gui.WindowFromPoint((rect[0]+2,rect[1]+2))!=h, 'Empty pixel blocked underlying window'
            assert win32gui.WindowFromPoint((x,y))==h, 'Body was not hit-testable'
            win32api.SetCursorPos((x,y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
            time.sleep(.1)
            win32api.SetCursorPos((x-60,y))
            time.sleep(.2)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)
            time.sleep(.1)
            moved=win32gui.GetWindowRect(h)
            assert moved[0] < rect[0]-20, (rect,moved)
            controls.entry.delete(0,'end')
            controls.entry.insert(0,'Hello Alex. I am testing my desktop voice and pause control.')
            controls.speak()
            state.update(phase='speech',window=h)
            print('PASS transparent pixels, body hit test, topmost, main stage hidden, dragging',flush=True)
        elif state['phase']=='speech' and controls.bridge.speech.state=='playing':
            state.update(phase='pause',at=time.monotonic()+.7)
        elif state['phase']=='pause' and time.monotonic()>state['at']:
            controls.pause()
            assert controls.bridge.behavior.paused and controls.bridge.speech.state=='idle'
            state.update(phase='verify_pause',at=time.monotonic()+.3)
        elif state['phase']=='verify_pause' and time.monotonic()>state['at']:
            snap=json.loads((controls.folder/'behavior.json').read_text())
            assert snap['paused'] and snap['mouth_open']==0
            controls.pause()
            assert not controls.bridge.behavior.paused
            print('PASS speech playback, pause stop, zero jaw and resume',flush=True)
            win32gui.PostMessage(state['window'],win32con.WM_NCRBUTTONUP,win32con.HTCAPTION,0)
            state['phase']='closing'
        root.after(100,step)
    except Exception as exc:
        errors.append(repr(exc))
        controls.close()
root.after(100,step)
root.mainloop()
assert not errors, errors
assert state['phase']=='closing', state
assert controls.process.poll() is not None and controls.bridge.speech.state=='idle'
assert not win32gui.IsWindow(state['window'])
print('PASS right-click close removed renderer, overlay and controls',flush=True)
print('Evidence:',controls.folder,flush=True)

"""Local window placement and optional, explicitly selected animation cues."""
import math
import os


def move(window, x, y):
    """Use absolute Windows coordinates, including monitors left of primary."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        api = ctypes.windll.user32
        api.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        api.GetAncestor.restype = wintypes.HWND
        api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, wintypes.UINT]
        api.SetWindowPos(api.GetAncestor(window.winfo_id(), 2), None, int(x), int(y), 0, 0, 0x0015)
    else:
        window.geometry(f"+{max(0, int(x))}+{max(0, int(y))}")


def dock_position(area, width, height, side):
    left, top, right, bottom = area
    width, height = min(width, right - left), min(height, bottom - top)
    x = left + 12 if side == "left" else right - width - 12
    return min(right - width, max(left, x)), max(top, bottom - height - 12), width, height


def dock(window, side):
    window.update_idletasks()
    area = (0, 0, window.winfo_screenwidth(), window.winfo_screenheight())
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class MonitorInfo(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                        ("work", wintypes.RECT), ("flags", wintypes.DWORD)]
        api = ctypes.windll.user32
        api.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        api.GetAncestor.restype = wintypes.HWND
        api.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        api.MonitorFromWindow.restype = wintypes.HANDLE
        api.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, wintypes.UINT]
        hwnd = api.GetAncestor(window.winfo_id(), 2)
        info = MonitorInfo()
        info.size = ctypes.sizeof(info)
        if api.GetMonitorInfoW(api.MonitorFromWindow(hwnd, 2), ctypes.byref(info)):
            area = (info.work.left, info.work.top, info.work.right, info.work.bottom)
        x, y, w, h = dock_position(area, window.winfo_width(), window.winfo_height(), side)
        api.SetWindowPos(hwnd, None, x, y, w, h, 0x0014)
    else:
        x, y, w, h = dock_position(area, window.winfo_width(), window.winfo_height(), side)
        window.geometry(f"{w}x{h}+{x}+{y}")


def decorate(canvas):
    canvas.delete("decoration")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    if canvas.paused:
        return
    phase = 0 if canvas.reduced else math.sin(canvas.tick / 8)
    x, y = w * .78, h * .17 + phase * 2
    color = "#76D9E8" if canvas.effect == "hologram" else "#C3A7FF"
    if canvas.mood == "happy":
        points = []
        for i in range(10):
            radius = 11 if i % 2 == 0 else 5
            points.extend((x + math.cos(i * math.pi / 5 - math.pi / 2) * radius,
                           y + math.sin(i * math.pi / 5 - math.pi / 2) * radius))
        canvas.create_polygon(points, fill=color, outline="", tags="decoration")
    elif canvas.mood == "thoughtful":
        for i in range(3):
            canvas.create_oval(x + i * 7, y, x + i * 7 + 4, y + 4, fill=color, outline="", tags="decoration")
    elif canvas.mood == "focused":
        canvas.create_oval(x - 9, y - 9, x + 9, y + 9, outline=color, width=2, tags="decoration")
        canvas.create_line(x - 14, y, x + 14, y, fill=color, tags="decoration")
        canvas.create_line(x, y - 14, x, y + 14, fill=color, tags="decoration")
    elif canvas.mood == "sleepy":
        canvas.create_text(x, y, text="z Z", fill=color, font=("Segoe UI", 13), tags="decoration")
    elapsed = canvas.tick - canvas.arrival
    if not canvas.reduced and 0 <= elapsed < 24:
        radius = 14 + elapsed * 2
        canvas.create_oval(w / 2 - radius, h - 28, w / 2 + radius, h - 14,
                           outline=color, width=2, tags="decoration")
        canvas.move("body", 0, (1 - elapsed / 24) ** 2 * -30)

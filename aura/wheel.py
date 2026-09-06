"""Shift-held controls over Aura; reads only modifier state, never typed text."""
import math
import os


class ControlWheel:
    def __init__(self, canvas, actions):
        self.canvas, self.actions = canvas, actions
        canvas.control_wheel = self
        self.job = None
        self.key = None
        self.pinned = False
        self.canvas.bind("<Destroy>", self.stop, add="+")
        self.poll()

    def show(self):
        canvas = self.canvas
        w, h = canvas.winfo_width(), canvas.winfo_height()
        key = (w, h)
        if self.key == key and canvas.find_withtag("wheel"):
            canvas.tag_raise("wheel")
            return
        self.hide()
        self.key = key
        radius = min(100, w / 2 - 34)
        for i, (label, command) in enumerate(self.actions):
            angle = -math.pi / 2 + i * math.tau / len(self.actions)
            x, y = w / 2 + math.cos(angle) * radius, h / 2 + math.sin(angle) * radius
            tag = "wheel-" + str(i)
            canvas.create_oval(x-29, y-24, x+29, y+24, fill="#222A40", outline="#B6A0FF", width=1,
                               tags=("wheel", tag))
            canvas.create_text(x, y, text=label, fill="#F0F1F8", font=("Segoe UI", 9, "bold"), tags=("wheel", tag))
            def choose(event, action=command):
                self.pinned = False
                self.hide()
                action()
                return "break"
            canvas.tag_bind(tag, "<ButtonPress-1>", choose)

    def hide(self):
        if self.canvas.winfo_exists():
            self.canvas.delete("wheel")
        self.key = None

    def toggle(self):
        """Explicit button access remains available without modifier polling."""
        self.pinned = not self.pinned
        self.show() if self.pinned else self.hide()

    def poll(self):
        if not self.canvas.winfo_exists():
            return
        held = False
        if os.name == "nt":
            import ctypes
            held = bool(ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000)
        x, y = self.canvas.winfo_pointerxy()
        inside = (self.canvas.winfo_rootx() <= x < self.canvas.winfo_rootx() + self.canvas.winfo_width() and
                  self.canvas.winfo_rooty() <= y < self.canvas.winfo_rooty() + self.canvas.winfo_height())
        if (self.pinned or held and inside) and self.canvas.winfo_viewable():
            self.show()
        elif self.key is not None:
            self.hide()
        self.job = self.canvas.after(60, self.poll)

    def stop(self, event=None):
        if event is None or event.widget is self.canvas:
            if self.job:
                self.canvas.after_cancel(self.job)
                self.job = None

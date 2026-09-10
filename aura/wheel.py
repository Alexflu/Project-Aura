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
        self.selected = 0
        self.previous_focus = None
        for key in ("Left", "Up", "Right", "Down", "Return", "space", "Escape"):
            self.canvas.bind("<" + key + ">", self.on_key, add="+")
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
                               tags=("wheel", tag, tag + "-outline"))
            canvas.create_text(x, y, text=label, fill="#F0F1F8", font=("Segoe UI", 9, "bold"), tags=("wheel", tag))
            def choose(event, action=command):
                self.dismiss()
                action()
                return "break"
            canvas.tag_bind(tag, "<ButtonPress-1>", choose)
        self.highlight()

    def highlight(self):
        for i in range(len(self.actions)):
            selected = self.pinned and i == self.selected
            self.canvas.itemconfigure("wheel-" + str(i) + "-outline",
                                      outline="#FFFFFF" if selected else "#B6A0FF",
                                      width=3 if selected else 1)

    def dismiss(self):
        self.pinned = False
        self.hide()
        previous, self.previous_focus = self.previous_focus, None
        if previous is not None and previous.winfo_exists():
            previous.focus_set()

    def on_key(self, event):
        # Let the application's Ctrl+Space shortcut reach its global binding.
        if event.state & 0x0004:
            return
        if not self.pinned or self.key is None:
            return
        if event.keysym == "Escape":
            self.dismiss()
        elif event.keysym in ("Return", "space"):
            action = self.actions[self.selected][1]
            self.dismiss()
            action()
        else:
            step = -1 if event.keysym in ("Left", "Up") else 1
            self.selected = (self.selected + step) % len(self.actions)
            self.highlight()
        return "break"

    def hide(self):
        if self.canvas.winfo_exists():
            self.canvas.delete("wheel")
        self.key = None

    def toggle(self):
        """Explicit button access remains available without modifier polling."""
        if self.pinned:
            self.dismiss()
        else:
            self.previous_focus = self.canvas.focus_get()
            self.selected = 0
            self.pinned = True
            self.show()
            self.highlight()
            self.canvas.focus_set()

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

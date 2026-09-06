"""AuraShell: original, parameterized 2D artwork; no downloaded character assets."""
import math
import time
from .motion import Motion
import tkinter as tk

PALETTES = {
    "violet": ("#B6A0FF", "#6452AA", "#221D3E"),
    "ocean": ("#76D9E8", "#307C9A", "#163342"),
    "forest": ("#9BDDAD", "#447A5A", "#213A30"),
    "ember": ("#FFBF8B", "#B87348", "#432B28"),
    "rose": ("#F3A7CE", "#A55987", "#422B40"),
    "slate": ("#C8D4DF", "#667D94", "#293747"),
}
BG = "#10151F"


def draw_avatar(canvas, look, tick=0, reduced=False):
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 100), max(canvas.winfo_height(), 100)
    scale = min(w / 360, h / 440)
    ox, oy = (w - 360 * scale) / 2, (h - 440 * scale) / 2
    bounce = 0 if reduced else math.sin(tick / 6) * 2.5
    accent, mid, deep = PALETTES[look["palette"]]
    def coords(values):
        return [((x + ox / scale) if i % 2 == 0 else (x + oy / scale + bounce)) * scale for i, x in enumerate(values)]
    def oval(*v, **kw):
        return canvas.create_oval(*coords(v), width=0, **kw)
    def poly(*v, **kw):
        return canvas.create_polygon(*coords(v), **kw)
    def line(*v, **kw):
        return canvas.create_line(*coords(v), **kw)
    oval(44, 65, 316, 342, fill=deep)
    oval(64, 85, 296, 322, fill="#18202C")
    oval(92, 397, 268, 414, fill="#080D15")
    for x, y, r in ((57, 175, 3), (295, 132, 4), (276, 311, 3), (86, 300, 2)):
        oval(x-r, y-r, x+r, y+r, fill=accent)
    # Silhouette changes alter limb length without altering the protected face.
    delta = {"balanced": 0, "compact": -17, "tall": 15}[look["silhouette"]]
    foot = 387 + delta / 3
    poly(143, 296, 177, 296, 171, foot, 147, foot, fill="#252D41", smooth=True)
    poly(183, 296, 216, 296, 213, foot, 189, foot, fill="#303951", smooth=True)
    oval(133, foot-12, 177, foot+13, fill="#101826")
    oval(184, foot-12, 227, foot+13, fill="#101826")
    line(141, foot+5, 169, foot+5, fill=accent, width=3*scale)
    line(193, foot+5, 221, foot+5, fill=accent, width=3*scale)
    # Hair behind the body.
    if look["hair"] == "long":
        poly(123, 104, 237, 105, 254, 253, 213, 288, 111, 263, fill="#29243D", smooth=True)
    elif look["hair"] == "bob":
        oval(117, 87, 245, 228, fill="#29243D")
    # Arms, jacket, hands.
    poly(133, 211, 117, 224, 102, 291, 119, 299, 148, 241, fill=mid, smooth=True)
    poly(226, 211, 244, 222, 257, 290, 241, 300, 212, 241, fill=mid, smooth=True)
    oval(101, 282, 122, 308, fill="#EBC3AF")
    oval(239, 282, 260, 308, fill="#EBC3AF")
    outfit = look["outfit"]
    body_color = mid if outfit in ("explorer", "casual") else "#354351"
    poly(149, 199, 211, 199, 231, 235, 218, 312, 141, 312, 127, 235, fill=body_color, smooth=True)
    poly(162, 195, 198, 195, 197, 222, 181, 232, 163, 218, fill="#DDB29E", smooth=True)
    if outfit == "engineer":
        poly(142, 216, 155, 218, 155, 256, 207, 256, 207, 218, 218, 216, 221, 310, 140, 310, fill=accent)
        poly(161, 266, 202, 266, 200, 286, 164, 286, fill=mid)
        line(169, 270, 169, 280, fill="#F9E8CF", width=3*scale)
    elif outfit == "tactical":
        poly(151, 221, 210, 221, 216, 301, 143, 301, fill=deep)
        for x in (149, 184):
            poly(x, 258, x+27, 258, x+27, 284, x, 284, fill=mid)
        line(146, 242, 216, 242, fill=accent, width=4*scale)
    elif outfit == "explorer":
        poly(149, 208, 177, 234, 158, 268, 139, 226, fill=accent)
        poly(211, 208, 183, 234, 202, 267, 222, 226, fill=accent)
        line(181, 235, 181, 306, fill=deep, width=2*scale)
    else:
        poly(167, 248, 183, 240, 198, 248, 192, 266, 180, 273, 169, 264, fill=accent)
    # Face and fringe.
    oval(124, 102, 237, 209, fill="#EBC3AF")
    poly(122, 146, 124, 98, 163, 80, 221, 87, 242, 139, 216, 119, 193, 122,
         162, 111, 141, 148, fill="#35304D", smooth=True)
    if look["hair"] == "pixie":
        poly(128, 113, 140, 78, 179, 94, 210, 78, 238, 120, 198, 109, 159, 127, fill="#35304D", smooth=True)
    line(135, 114, 149, 103, 164, 100, fill=accent, width=3*scale, smooth=True)
    blink = not reduced and tick % 52 in (0, 1)
    for x in (155, 208):
        if blink:
            line(x-7, 163, x+7, 164, fill="#34304B", width=3*scale)
        else:
            oval(x-8, 153, x+8, 170, fill="#FBF4EF")
            oval(x-4, 154, x+5, 169, fill=mid)
            oval(x-2, 156, x+3, 166, fill="#222333")
            oval(x-1, 156, x+2, 159, fill="#FFFFFF")
    level = getattr(canvas, "audio_level", None)
    talking = level is not None and level > .16
    if not reduced and (talking or (level is None and getattr(canvas, "expression", "idle") == "speaking" and tick % 8 < 5)):
        oval(174, 181, 189, 193, fill="#713E55")
    else:
        line(174, 185, 180, 188, 188, 184, fill="#A26368", smooth=True, width=2*scale)
    oval(137, 173, 151, 179, fill="#DEA6A0")
    oval(214, 173, 228, 179, fill="#DEA6A0")
    accessory = look["accessory"]
    if accessory == "headphones":
        canvas.create_arc(*coords((115, 85, 248, 197)), start=0, extent=180, style="arc", outline=accent, width=6*scale)
        oval(115, 142, 132, 181, fill=accent)
        oval(234, 142, 251, 181, fill=accent)
    elif accessory == "goggles":
        line(128, 125, 233, 125, fill=accent, width=5*scale)
        for x in (146, 190):
            oval(x, 111, x+32, 134, fill=accent)
            oval(x+4, 114, x+28, 131, fill="#23495B")
    elif accessory == "leaf":
        poly(224, 113, 243, 84, 253, 101, 224, 113, fill="#A2D9AF", smooth=True)
        line(224, 113, 246, 96, fill="#44795B", width=2*scale)


class Avatar(tk.Canvas):
    def __init__(self, master, look, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self.look = look.copy()
        self.expression = "idle"
        self.audio_level = None
        self.mood = "neutral"
        self.effect = "solid"
        self.arrival = -100
        self.reduced = False
        self.paused = False
        self.motion = Motion()
        self.pointer = 0
        self.motion_strength = 1.0
        self.last_frame = time.monotonic()
        self.tick = 2
        self.job = None
        self.bind("<Destroy>", self.stop)
        self.bind("<Motion>", lambda e: setattr(self, "pointer", (e.x / max(1, self.winfo_width()) - .5) * 2))
        self.bind("<Leave>", lambda e: setattr(self, "pointer", 0))
        self.animate()

    def animate(self):
        if self.winfo_exists():
            now = time.monotonic()
            if not self.winfo_viewable() or self.winfo_width() < 10 or self.winfo_height() < 10:
                self.last_frame = now
                self.job = self.after(33, self.animate)
                return
            self.motion.update(now - self.last_frame, self.audio_level, self.expression == "speaking",
                               self.pointer, self.paused or self.reduced, self.mood)
            self.last_frame = now
            if not self.paused and not self.reduced:
                self.tick = int(self.motion.time * 20) + 2
            if getattr(self,"model",None) is not None:
                from .models import draw
                draw(self)
            elif self.look["outfit"] in ("tactical", "stealth"):
                from .illustrated import draw
                draw(self)
            else:
                self.stage_key = None
                draw_avatar(self, self.look, self.tick, self.reduced or self.paused)
            from .presence import decorate
            decorate(self)
            wheel = getattr(self, "control_wheel", None)
            if wheel and wheel.key is not None:
                wheel.show()
            interval = 33 if not self.reduced and not self.paused else 150
            spent = int((time.monotonic() - now) * 1000)
            # Let Tk finish mapping tabs/windows before the next expensive frame.
            # Multiple animated surfaces can otherwise starve its idle geometry work.
            self.job = self.after(max(16, interval - spent), self.defer_frame)

    def defer_frame(self):
        self.job = self.after_idle(self.animate)

    def stop(self, event=None):
        if self.job:
            self.after_cancel(self.job)
            self.job = None

    def wake(self):
        """Refresh a newly mapped surface without starting another timer loop."""
        self.stop()
        if self.winfo_exists():
            self.last_frame = time.monotonic()
            self.job = self.after_idle(self.animate)

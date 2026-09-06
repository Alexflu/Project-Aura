"""Runtime matte, independent face layers and bounded 2D deformation.

Original artwork stays untouched on disk. The renderer removes its known navy
backdrop and caches static appearance layers separately from motion.
"""
from functools import lru_cache
from pathlib import Path
import math
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter

ASSET = Path(__file__).with_name("assets") / "aura-atlas-v1.png"


@lru_cache(maxsize=1)
def atlas():
    with Image.open(ASSET) as source:
        return source.convert("RGB")


@lru_cache(maxsize=12)
def layers(column, palette, effect):
    source = atlas()
    left = column * 256
    base = source.crop((left, 20, left + 256, 540))
    cx = (144, 382, 630, 870)[column]
    colors = {"violet": None, "ocean": (90, 215, 240), "forest": (110, 210, 145),
              "ember": (240, 110, 80), "rose": (240, 130, 190), "slate": (175, 205, 230)}
    target = colors[palette]
    variants = []
    for offset in (0, 520, 1020):
        result = base.copy()
        if offset:
            box = (cx - 20, 87, cx + 17, 122)
            result.paste(source.crop((box[0], box[1] + offset, box[2], box[3] + offset)),
                         (box[0] - left, box[1] - 20))
        alpha = Image.new("L", result.size, 255)
        pixels, coverage = result.load(), alpha.load()
        for y in range(result.height):
            for x in range(result.width):
                r, g, b = pixels[x, y]
                # This versioned atlas has a narrow blue backdrop range. Avoid
                # luminance-only keying, which would remove the black clothes.
                background = r < 22 and 10 <= g <= 28 and 22 <= b <= 45 and 3 <= g-r <= 10 and 9 <= b-g <= 20
                if background:
                    coverage[x, y] = 0
                elif target and b > g * 1.3 and r > g * 1.15 and b > 45 and r > 35:
                    strength = min(1, max(r, b) / 210)
                    pixels[x, y] = tuple(int(c * strength) for c in target)
        if effect == "hologram":
            luminance = ImageOps.grayscale(result)
            glow = luminance.point(lambda value: min(255, max(0, value - 15) * 3))
            result = ImageOps.colorize(glow, "#102432", "#82EBFF")
            pixels = result.load()
            for y in range(0, result.height, 5):
                for x in range(result.width):
                    if coverage[x, y]:
                        pixels[x, y] = tuple(int(v * .7) for v in pixels[x, y])
        result.putalpha(alpha)
        variants.append(result)
    # Independently feathered eye and mouth regions eliminate rectangular face swaps.
    masks = []
    for box in ((cx-left-19, 68, cx-left+17, 86), (cx-left-16, 87, cx-left+12, 103)):
        mask = Image.new("L", base.size)
        ImageDraw.Draw(mask).rounded_rectangle(box, radius=3, fill=255)
        masks.append(mask.filter(ImageFilter.GaussianBlur(1)))
    return (*variants, *masks)


@lru_cache(maxsize=48)
def face_frame(column, mouth, blink, palette, width, height, effect):
    idle, closed, speaking, eyes_mask, mouth_mask = layers(column, palette, effect)
    result = idle
    if mouth:
        # Use the authored open mouth at full opacity: interpolating the
        # drawings doubles the lips, while compressing this flat atlas pulls
        # the jaw into the mouth. True intermediate shapes need authored art.
        result = Image.composite(speaking, idle, mouth_mask)
    if blink:
        mix = Image.blend(idle, closed, blink / 3)
        result = Image.composite(mix, result, eyes_mask)
    return result.resize((width, height), Image.Resampling.LANCZOS)


def frame(column, expression, palette, width, height, effect="solid"):
    return face_frame(column, 4 if expression == "speaking" else 0,
                      3 if expression == "blink" else 0, palette, width, height, effect)


def deform(image, motion, strength, mood, look=None):
    width, height = image.size
    mesh = []
    column = ((2 if look["hair"] == "long" else 0) + (look["outfit"] == "stealth")) if look else 0
    center = (144, 126, 118, 102)[column]
    def point(x, y):
        logical_x, logical_y = x*256/width, y*520/height
        dx, dy = motion.offset(logical_y, strength, mood)
        if look:
            sx, sy = motion.secondary_offset(logical_x, logical_y, center, look["hair"], look["outfit"])
            dx, dy = dx + sx*strength, dy + sy*strength
        return x-dx*width/256, y-dy*height/520
    step_y, step_x = max(8, height//22), max(8, width//6)
    for y0 in range(0, height, step_y):
        y1 = min(height, y0+step_y)
        for x0 in range(0, width, step_x):
            x1 = min(width, x0+step_x)
            quad = (*point(x0,y0), *point(x0,y1), *point(x1,y1), *point(x1,y0))
            mesh.append(((x0,y0,x1,y1), quad))
    return image.transform(image.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)


def draw(canvas):
    look = canvas.look
    width, height = max(100, canvas.winfo_width()), max(100, canvas.winfo_height())
    scale = min((width - 24) / 256, (height - 24) / 520)
    size = (max(1, int(256 * scale)), max(1, int(520 * scale)))
    column = (2 if look["hair"] == "long" else 0) + (look["outfit"] == "stealth")
    still = canvas.reduced or canvas.paused
    mouth = 0 if still else round(canvas.motion.mouth * 4)
    blink = 0 if still else round(canvas.motion.blink * 3)
    sprite = face_frame(column, mouth, blink, look["palette"], *size, canvas.effect)
    if getattr(canvas, "equipment", None):
        from .equipment import paint
        sprite = sprite.copy()
        from .motion import ease
        elapsed = max(0, min(.2, canvas.motion.time-getattr(canvas, "item_reveal_updated", canvas.motion.time)))
        canvas.item_reveal_updated = canvas.motion.time
        canvas.item_reveal = ease(getattr(canvas, "item_reveal", 0),
                                 float(getattr(canvas, "item_revealed", False)), elapsed if not still else 0, 5)
        paint(ImageDraw.Draw(sprite), canvas.equipment, (144,126,118,102)[column]*size[0]/256,
              0, size[0]/256, canvas.motion.time, getattr(canvas, "item_reveal", 0),
              -1 if still else canvas.motion.time-getattr(canvas, "cast_started", -100))
    if not still:
        sprite = deform(sprite, canvas.motion, canvas.motion_strength, canvas.mood, look)
    # Upload into the hidden buffer: updating a displayed Tk image is expensive.
    if getattr(canvas, "photo_size", None) != sprite.size:
        canvas.photo_buffers = [ImageTk.PhotoImage(sprite, master=canvas), ImageTk.PhotoImage(sprite, master=canvas)]
        canvas.photo_size = sprite.size
        canvas.photo_index = 0
    else:
        canvas.photo_index = 1 - canvas.photo_index
        canvas.photo_buffers[canvas.photo_index].paste(sprite)
    canvas.sprite_photo = canvas.photo_buffers[canvas.photo_index]
    stage_key = (width, height, canvas.effect, getattr(canvas, "desktop_mode", False))
    rebuild = getattr(canvas, "stage_key", None) != stage_key
    if rebuild:
        canvas.delete("all")
        canvas.stage_key = stage_key
    if rebuild and not getattr(canvas, "desktop_mode", False):
        target = (19, 32, 42) if canvas.effect == "hologram" else (27, 25, 40)
        for i in range(20):
            t = i / 19
            rgb = tuple(round(a + (b-a)*t) for a,b in zip((16,21,31), target))
            color = "#%02x%02x%02x" % rgb
            inset = t * .20
            canvas.create_oval(width*(.04+inset), height*(.04+inset), width*(.96-inset), height*(.92-inset), fill=color, outline="")
        canvas.create_oval(width*.29, height*.94, width*.71, height*.97, fill="#080C14", outline="")
    if rebuild:
        canvas.body_id = canvas.create_image(width / 2, height / 2, image=canvas.sprite_photo, tags="body")
    else:
        canvas.itemconfigure(canvas.body_id, image=canvas.sprite_photo)
        canvas.coords(canvas.body_id, width / 2, height / 2)



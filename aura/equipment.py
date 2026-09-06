"""Bounded, declarative visual equipment. Items never execute code or tasks."""
import copy
import json
import math
import re
from pathlib import Path
from .core import AuraError

SLOTS = ("holster", "back", "charm", "spell")
KINDS = ("dagger", "bag", "crystal", "fire", "ice", "lightning")
BUILTINS = [
    dict(id="aura.dagger", name="Hidden dagger", slot="holster", kind="dagger", color="#B6A0FF"),
    dict(id="aura.bag", name="Field satchel", slot="back", kind="bag", color="#7DA6B8"),
    dict(id="aura.crystal", name="Arcane focus", slot="charm", kind="crystal", color="#B6A0FF"),
    dict(id="aura.fire", name="Ember spiral", slot="spell", kind="fire", color="#FF995E"),
    dict(id="aura.ice", name="Frost halo", slot="spell", kind="ice", color="#83E4FF"),
    dict(id="aura.lightning", name="Storm circuit", slot="spell", kind="lightning", color="#CFABFF"),
]
for _item in BUILTINS:
    _item.update(schema=1, author="Project Aura", license="MIT")


def validate_item(item):
    keys = {"schema", "id", "name", "slot", "kind", "color", "author", "license"}
    if not isinstance(item, dict) or set(item) != keys or type(item["schema"]) is not int or item["schema"] != 1:
        raise AuraError("Use a version 1 Aura item with exactly the documented fields.")
    if not isinstance(item["id"], str) or not re.fullmatch(r"[a-z][a-z0-9_.-]{2,63}", item["id"]):
        raise AuraError("Item IDs use 3–64 lowercase letters, numbers, dots, hyphens or underscores.")
    for key in ("name", "author", "license"):
        if not isinstance(item[key], str) or not 1 <= len(item[key]) <= 100 or any(ord(c) < 32 for c in item[key]):
            raise AuraError("Item name, author and license must be short, printable text.")
    if item["kind"] not in KINDS or item["slot"] not in SLOTS:
        raise AuraError("Unsupported item kind or equipment slot.")
    expected = {"dagger": "holster", "bag": "back", "crystal": "charm"}.get(item["kind"], "spell")
    if item["slot"] != expected:
        raise AuraError("This item is not compatible with that slot.")
    if not isinstance(item["color"], str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", item["color"]):
        raise AuraError("Use a six-digit hexadecimal item color.")
    return dict(item)


class Inventory:
    def __init__(self, path):
        self.path = Path(path)
        self.custom, self.equipped, self.history = [], {}, []
        if self.path.exists():
            if self.path.stat().st_size > 65536:
                raise AuraError("Equipment data exceeds the supported size.")
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if set(data) != {"schema", "items", "equipped"} or data["schema"] != 1 or not isinstance(data["items"], list) or len(data["items"]) > 64:
                    raise ValueError()
                self.custom = [validate_item(item) for item in data["items"]]
                ids = [item["id"] for item in self.items]
                if len(set(ids)) != len(ids) or any(item["id"].startswith("aura.") for item in self.custom):
                    raise ValueError()
                if not isinstance(data["equipped"], dict):
                    raise ValueError()
                for slot, item_id in data["equipped"].items():
                    item = self.get(item_id)
                    if slot != item["slot"]:
                        raise ValueError()
                self.equipped = data["equipped"]
            except (ValueError, TypeError, KeyError) as exc:
                raise AuraError("Equipment data could not be read. The original file has been preserved.") from exc

    @property
    def items(self):
        return BUILTINS + self.custom

    def get(self, item_id):
        for item in self.items:
            if item["id"] == item_id:
                return dict(item)
        raise AuraError("That equipment item is unavailable.")

    def selected(self):
        return [self.get(item_id) for item_id in self.equipped.values()]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(dict(schema=1, items=self.custom, equipped=self.equipped), indent=2), encoding="utf-8")
        temp.replace(self.path)

    def equip(self, item_id):
        item = self.get(item_id)
        before = dict(self.equipped)
        if self.equipped.get(item["slot"]) == item_id:
            del self.equipped[item["slot"]]
        else:
            self.equipped[item["slot"]] = item_id
        try:
            self.save()
        except OSError:
            self.equipped = before
            raise
        self.history = (self.history + [before])[-20:]

    def undo(self):
        if not self.history:
            raise AuraError("No equipment change to undo in this session.")
        before = self.equipped
        self.equipped = dict(self.history[-1])
        try:
            self.save()
        except OSError:
            self.equipped = before
            raise
        self.history.pop()

    def import_item(self, path):
        path = Path(path)
        if path.stat().st_size > 8192:
            raise AuraError("Choose an item JSON smaller than 8 KB.")
        try:
            item = validate_item(json.loads(path.read_text(encoding="utf-8")))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise AuraError("Choose a valid UTF-8 item JSON.") from exc
        if item["id"].startswith("aura.") or any(other["id"] == item["id"] for other in self.items):
            raise AuraError("Choose a unique ID outside the reserved aura. namespace.")
        if len(self.custom) >= 64:
            raise AuraError("This beta supports up to 64 imported items.")
        self.custom.append(item)
        try:
            self.save()
        except OSError:
            self.custom.pop()
            raise
        return item

    def reset(self):
        self.path.unlink(missing_ok=True)
        self.custom, self.equipped, self.history = [], {}, []


def paint(draw, items, x, y, scale, t, reveal=0, cast=-1):
    """Shared procedural sockets/effects for desktop and cinematic playback."""
    def box(a,b,c,d):
        return (x+a*scale, y+b*scale, x+c*scale, y+d*scale)
    def line(points, fill, width=2):
        draw.line([(x+a*scale,y+b*scale) for a,b in points], fill=fill, width=max(1,round(width*scale)))
    def poly(points, fill, outline=None):
        draw.polygon([(x+a*scale,y+b*scale) for a,b in points], fill=fill, outline=outline)
    for item in items:
        color, kind = item["color"], item["kind"]
        if kind == "bag":
            sway = math.sin(t*1.5)*1.2
            line([(-29,128),(22,265)], "#678293", 4)
            draw.rounded_rectangle(box(20+sway,239,46+sway,275), radius=max(2,round(4*scale)), fill="#263646", outline=color, width=max(1,round(scale)))
            line([(22+sway,248),(44+sway,248)],color)
            draw.rectangle(box(29+sway,246,35+sway,253),fill="#BECBD5")
        elif kind == "dagger":
            draw.rounded_rectangle(box(30,267,41,306),radius=max(1,round(3*scale)),fill="#182333",outline=color)
            amount = max(0,min(1,reveal))
            dx,dy=amount*28, -amount*58
            poly([(32+dx,267+dy),(38+dx,267+dy),(37+dx,299+dy),(35+dx,307+dy),(33+dx,299+dy)],"#BBC9DE",color)
            line([(35+dx,260+dy),(35+dx,272+dy)],"#283044",5)
            line([(29+dx,271+dy),(41+dx,271+dy)],color,2)
        elif kind == "crystal":
            cx=-48+math.sin(t*1.3)*2;cy=190+math.cos(t*1.7)*4
            poly([(cx,cy-13),(cx+7,cy),(cx,cy+13),(cx-7,cy)],color,"#DCE3FF")
            line([(cx,cy-11),(cx+2,cy),(cx,cy+11)],"#FFFFFF",1)
        elif cast >= 0 and cast < 3.4:
            strength = math.sin(math.pi*min(1,cast/3.4))
            radius=(18+cast*16)*strength
            cx,cy=-65,178
            for ring in range(3):
                r=radius+ring*4
                draw.ellipse(box(cx-r,cy-r*.4,cx+r,cy+r*.4),outline=color,width=max(1,round(scale)))
            for i in range(18):
                a=i*math.tau/18+t*(1 if kind=="fire" else -.65)
                r=radius*(.45+(i%3)*.25)
                px,py=cx+math.cos(a)*r,cy+math.sin(a)*r*.75
                if kind=="ice":
                    poly([(px,py-6),(px+3,py),(px,py+6),(px-3,py)],color)
                elif kind=="lightning":
                    line([(cx,cy),(px*.45+cx*.55+math.sin(i+t*17)*5,py*.5+cy*.5),(px,py)],color,1)
                else:
                    py-=((t*20+i*7)%28)*strength
                    poly([(px-2,py+5),(px+3,py+3),(px+math.sin(t*7+i)*3,py-7)],color)

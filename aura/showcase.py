"""Deterministic local cinematic. The desktop player and video exporter share frames.

This is an optional performance stage, never a simulated tool approval or task.
"""
from functools import lru_cache
import math
from pathlib import Path
import time
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk
from .illustrated import face_frame, deform
from .motion import Motion
from .equipment import BUILTINS, paint
from .voice import Clip, Speech

WIDTH, HEIGHT, DURATION = 960, 540, 64
ASSETS = Path(__file__).with_name("assets")
CHAPTERS = (
    (0, "Arrival", "A little dramatic?", "Helicopter entry, sparks and a soft landing.\nA local performance on Aura's stage."),
    (12, "Presence", "New body. Same Aura.", "Breathing, blinking and gentle hair motion.\nAn illustrated body with a holographic mode."),
    (21, "Appearance", "Make it feel like you.", "Tactical Ops or Stealth Striker.\nShort or long hair. Six accent palettes."),
    (30, "Equipment", "A few useful secrets.", "Holster, satchel and arcane focus.\nEquip, remove, save and undo."),
    (39, "Spellbook", "Choose your element.", "Fire, ice or lightning.\nLocal visual spells, with no app permissions."),
    (48, "Voice & connection", "Let's work together.", "Local speech and WAV mouth movement.\nMCP requests stay subject to your approval."),
    (57, "Create", "Help me grow.", "Build creator items. Improve my rig.\nContribute code, artwork and testing."),
)
# Timed local speech, also distributed as accessible captions in the video.
NARRATION = (
    (8, 12, "Okay. Perhaps that entrance was a little dramatic."),
    (13, 21, "I'm Aura. New body, same violet glow. Let's see what this version can do."),
    (22, 30, "Tactical jacket, or stealth gear? Short hair, or long? You choose my look and accent colors."),
    (31, 39, "A satchel, an arcane focus, and a hidden dagger. Equip a favorite, or undo the change."),
    (40, 48, "Fire, ice, or lightning. These are visual spells. Your files are perfectly safe."),
    (49, 57, "I can speak text locally. A connected MCP client can propose changes for your approval."),
    (58, 64, "This is Project Aura. Help build my next chapter."),
)


def smooth(value):
    value = max(0, min(1, value))
    return value*value*(3-2*value)


def chapter(t):
    return max(i for i, item in enumerate(CHAPTERS) if t >= item[0])


@lru_cache(maxsize=12)
def font(size, bold=False):
    filename = "segoeuib.ttf" if bold else "segoeui.ttf"
    try:
        return ImageFont.truetype(str(Path("C:/Windows/Fonts") / filename), size)
    except OSError:
        return ImageFont.load_default(size=size)


@lru_cache(maxsize=1)
def background():
    image = Image.new("RGB", (WIDTH,HEIGHT))
    d = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        amount = y / HEIGHT
        d.line((0,y,WIDTH,y), fill=(round(9+6*amount),round(12+8*amount),round(24+13*amount)))
    d.ellipse((100,30,720,520),fill="#13182D")
    for x in range(-300,1400,80):
        d.line((480+(x-480)*.2,360,x,540),fill="#20283E")
    for y in (366,380,403,437,490,539):
        d.line((0,y,960,y),fill="#20283E")
    return image


def text(d, xy, value, size=18, color="#EDECF9", bold=False):
    d.text(xy, value, font=font(size,bold), fill=color, spacing=9)


def spark(d, x,y,r, color):
    d.line((x-r,y,x+r,y),fill=color,width=1)
    d.line((x,y-r,x,y+r),fill=color,width=1)


def explosion(image, x, y, age, seed=0):
    if not 0 <= age < 2.8:
        return
    fx=Image.new("RGBA",image.size)
    d=ImageDraw.Draw(fx)
    for i in range(26):
        a=i*2.399+seed
        speed=30+(i%7)*13
        px=x+math.cos(a)*speed*age
        py=y+math.sin(a)*speed*age+age*age*25
        radius=max(1,(15+i%6)*max(0,1-age/2.8))
        alpha=round(180*max(0,1-age/2.8))
        color=(255,130+(i%4)*20,55,alpha) if age<1 else (103,91,130,alpha)
        d.ellipse((px-radius,py-radius,px+radius,py+radius),fill=color)
        if age<1.4:
            d.line((px,py,px-math.cos(a)*13,py-math.sin(a)*13),fill=(255,216,164,alpha),width=2)
    radius=12+age*90
    d.ellipse((x-radius,y-radius,x+radius,y+radius),outline=(255,192,129,round(max(0,100-age*90))),width=2)
    image.paste(fx,(0,0),fx)


def helicopter(t):
    """Original layered vector vehicle; no borrowed game assets."""
    im=Image.new("RGBA",(640,300))
    d=ImageDraw.Draw(im)
    d.polygon([(10,145),(210,129),(217,190),(14,173)],fill="#273345",outline="#6C7C96")
    d.polygon([(9,151),(5,99),(42,91),(61,166)],fill="#344257",outline="#8290A8")
    d.line((23,108,21,194),fill="#B8AECF",width=2)
    d.polygon([(208,112),(358,85),(451,103),(528,153),(529,199),(478,225),(254,228),(212,190)],fill="#303D52",outline="#9F9AB6")
    d.polygon([(362,94),(429,106),(480,145),(384,145)],fill="#233A4F",outline="#9DCAE6")
    d.line((409,105,432,143),fill="#6C9DAD",width=3)
    d.polygon([(488,150),(522,157),(522,188),(490,188)],fill="#172B3C",outline="#667F9C")
    d.rounded_rectangle((253,111,358,216),radius=6,fill="#090F1E",outline="#9C8BBA",width=2)
    for x in (241,369):
        d.line((x,113,x,215),fill="#5D6B7F",width=3)
    for y in (174,185,196):
        d.line((382,y,470,y),fill="#172335",width=2)
    for x in range(266,479,19):
        d.ellipse((x,217,x+2,219),fill="#9EACC0")
    d.line((267,226,253,248,473,248,490,237),fill="#9AA7BB",width=4)
    d.line((295,222,285,246),fill="#64748D",width=4)
    d.line((445,222,452,246),fill="#64748D",width=4)
    d.rectangle((303,67,341,87),fill="#3F4B60",outline="#A6AEC0")
    d.line((322,46,322,68),fill="#8291AD",width=5)
    angle=t*45
    for i in range(3):
        a=angle+i*math.tau/3
        dx=math.cos(a)*255;dy=math.sin(a)*15
        d.line((322-dx,45-dy,322+dx,45+dy),fill="#A1A8C3",width=3)
    d.arc((58,27,588,65),0,175,fill="#536178",width=1)
    d.ellipse((322,39,333,50),fill="#D2D6E5")
    text(d,(399,201),"AURA / 01",10,"#D6C7FF",True)
    d.ellipse((472,149,478,155),fill="#B8A1FF")
    d.ellipse((27,154,33,160),fill="#FF826F")
    return im


class Scene:
    def __init__(self, look, items=(), reduced=False):
        self.look=dict(look)
        self.items=list(items)
        self.reduced=reduced
        self.voice=None
        path=ASSETS/"tour-voice.wav"
        if path.exists():
            self.voice=Clip.read(path)

    def body(self, t, look, height, effect="solid", items=(), reveal=0, cast=-1):
        column=(2 if look["hair"]=="long" else 0)+(look["outfit"]=="stealth")
        level=self.voice.level(t) if self.voice else 0
        blink=3 if abs(t%5.3-3.2)<.1 and not self.reduced else 0
        mouth=4 if level>.12 and not self.reduced else 0
        sprite=face_frame(column,mouth,blink,look["palette"],256,520,effect).copy()
        paint(ImageDraw.Draw(sprite),items,(144,126,118,102)[column],0,1,t if not self.reduced else 0,reveal,cast if not self.reduced else -1)
        if not self.reduced:
            sprite=deform(sprite,Motion(time=t,gaze=math.sin(t*.6)*.45),1,"neutral",look)
        return sprite.resize((round(height*256/520),round(height)),Image.Resampling.LANCZOS)

    def frame(self, seconds):
        t=max(0,min(DURATION-.001,seconds))
        index=chapter(t)
        im=background().copy();d=ImageDraw.Draw(im)
        accent="#B6A0FF"
        text(d,(28,19),"PROJECT AURA",15,accent,True)
        text(d,(745,22),"LOCAL PERFORMANCE / BETA",10,"#8E99B8")
        for i in range(28):
            px=(i*173+19)%960; py=(i*79+45)%380
            sparkle=(math.sin(t*.8+i)+1)*.5 if not self.reduced else .25
            if sparkle>.65:
                spark(d,px,py,1+(i%2),"#786D9D")
        # A framed viewport makes the cinematic's boundary explicit.
        d.rounded_rectangle((23,56,936,483),radius=14,outline="#33314D",width=1)
        if index==0 and not self.reduced:
            self.arrival(im,t)
        else:
            look=dict(self.look)
            if look["outfit"] not in ("tactical","stealth"):
                look.update(outfit="stealth",hair="pixie")
            effect="hologram" if index==1 and t>=16 else "solid"
            if index==2:
                phase=min(2,int((t-21)/3))
                look.update(palette=("violet","ocean","ember")[phase],outfit=("tactical","stealth","stealth")[phase],hair=("pixie","pixie","long")[phase])
            items=list(self.items)
            if index==3:
                items=BUILTINS[:min(3,1+int((t-30)/2))]
            cast=-1
            if index==4:
                spell=BUILTINS[3+min(2,int((t-39)/3))]
                items=[BUILTINS[2],spell];cast=(t-39)%3
            height=414
            sprite=self.body(t,look,height,effect,items,smooth((t-34)/1.5) if index==3 else 0,cast)
            x=335; y=65
            im.paste(sprite,(x,y),sprite)
            d=ImageDraw.Draw(im)
            if index==1 and not self.reduced:
                scan=110+(t-12)*38%335
                d.line((330,scan,575,scan),fill="#7FCCE8",width=1)
                for sx in (324,583):
                    d.line((sx,100,sx,448),fill="#514B78",width=1)
                text(d,(290,457),"BODY SCAN / ILLUSTRATED RIG",10,"#A5BDDC")
            if index==2:
                for i,color in enumerate(("#B6A0FF","#76D9E8","#FFBF8B","#9BDDAD","#F3A7CE","#C8D4DF")):
                    d.ellipse((654+i*35,303,674+i*35,323),fill=color)
            if index==3:
                for i,item in enumerate(BUILTINS[:3]):
                    d.rounded_rectangle((648,304+i*39,893,337+i*39),radius=6,fill="#20263E",outline="#53476F")
                    text(d,(660,310+i*39),item["name"],14)
            if index==4:
                text(d,(650,316),BUILTINS[3+min(2,int((t-39)/3))]["name"],20,accent,True)
            if index==5:
                level=self.voice.level(t) if self.voice else 0
                for i in range(24):
                    h=4+level*(8+15*abs(math.sin(i*.8+t*3)))
                    d.line((650+i*9,330-h,650+i*9,330+h),fill=accent,width=3)
                text(d,(650,376),"This tour uses local Windows speech.",12,"#A8B4CE")
                text(d,(650,399),"Built-in GPT Voice is not connected.",12,"#A8B4CE")
            if index==6:
                text(d,(649,319),"github.com/Alexflu/Project-Aura",14,accent,True)
                text(d,(649,353),"OPEN SOURCE / MIT",12,"#A8B4CE")
                text(d,(649,380),"Source, beta and creator examples",12,"#A8B4CE")
            text(d,(650,124),f"0{index} / {CHAPTERS[index][1].upper()}",12,accent,True)
            # Headline wraps to preserve space for Aura at center stage.
            headline=CHAPTERS[index][2]
            words=headline.split();lines=[];line=""
            for word in words:
                candidate=(line+" "+word).strip()
                if d.textlength(candidate,font=font(27,True))>245 and line:
                    lines.append(line);line=word
                else:line=candidate
            lines.append(line)
            text(d,(648,155),"\n".join(lines),27,bold=True)
            text(d,(649,247),CHAPTERS[index][3],13,"#AFBAD2")
            text(d,(59,154),"AURA",31,accent,True)
            text(d,(60,203),"Digital familiar.\nDesktop collaborator.\nA work in progress.",14,"#9FACC8")
            text(d,(60,318),"REPLAY THIS TOUR\nIN THE WINDOWS BETA",11,"#A6A0C2",True)
        d=ImageDraw.Draw(im)
        for start,end,caption in NARRATION:
            if start<=t<end:
                length=d.textlength(caption,font=font(16))
                # Narration captions stay in their own full-width strip.
                d.rounded_rectangle((max(20,(960-length)/2-14),484,min(940,(960+length)/2+14),516),radius=6,fill="#111724")
                text(d,((960-length)/2,490),caption,16)
        d.line((28,532,932,532),fill="#30314C",width=3)
        d.line((28,532,28+904*t/DURATION,532),fill=accent,width=3)
        return im

    def arrival(self, im, t):
        d=ImageDraw.Draw(im)
        look=dict(self.look)
        if look["outfit"] not in ("tactical","stealth"):
            look.update(outfit="stealth",hair="pixie")
        text(d,(58,81),"INCOMING / AURA 01",13,"#B6A0FF",True)
        text(d,(681,448),"CINEMATIC STAGE / NO APP ACTION",10,"#AAA6C1")
        # Rocket one breaches a fictional stage panel, never the user's monitor.
        d.rounded_rectangle((709,162,867,301),radius=7,fill="#1D2639",outline="#727A99",width=2)
        text(d,(732,177),"WORKSPACE",13,"#ADBBD7",True)
        if t>=1.8:
            d.polygon([(728,195),(760,179),(783,193),(819,183),(835,218),(861,236),(836,258),(833,291),(798,272),(763,295),(751,258),(720,247)],fill="#090E1A",outline="#F5B57C")
        if .65<t<1.8:
            p=(t-.65)/1.15;x=-100+p*890;y=75+p*155
            d.line((x-100,y-21,x,y),fill="#FFD5AE",width=3)
            d.polygon([(x+14,y+3),(x-12,y-6),(x-16,y+2)],fill="#B5BFCF")
        explosion(im,792,231,t-1.8)
        hx=-610+smooth((t-2.2)/2.8)*880
        hy=100+math.sin(t*2)*3
        if t>8.3:
            hx+=smooth((t-8.3)/3.0)*720;hy-=smooth((t-8.3)/3.0)*220
        craft=helicopter(t)
        # Aura actually appears in the open door, ahead of the mounted prop.
        passenger=self.body(t,look,173)
        if t < 7.1:
            craft.paste(passenger,(263,65),passenger)
        cd=ImageDraw.Draw(craft)
        cd.line((302,191,331,218),fill="#78889F",width=5)
        cd.rounded_rectangle((306,171,341,187),radius=3,fill="#414C62",outline="#B3B4C8")
        for j in range(4):
            by=174+j*4+math.sin(t*55+j)*1.5
            cd.line((330,by,394,by),fill="#8B93A6",width=2)
        craft=craft.rotate(math.sin(t)*1.2,resample=Image.Resampling.BICUBIC,expand=False)
        im.paste(craft,(round(hx),round(hy)),craft)
        d=ImageDraw.Draw(im)
        if 5.1<t<6.8:
            muzzle=(hx+395,hy+181)
            if int(t*24)%3:
                d.polygon([(muzzle[0],muzzle[1]-4),(muzzle[0]+26,muzzle[1]),(muzzle[0],muzzle[1]+4)],fill="#FFE5A9")
                d.line((*muzzle,787+math.sin(t*71)*17,230+math.cos(t*63)*30),fill="#FFC982",width=1)
            for j in range(8):
                age=(t*3+j*.13)%1
                x=hx+312-age*45;y=hy+187+age*age*120
                d.line((x,y,x+4,y+2),fill="#CBA965",width=2)
            explosion(im,792,235,(t-5.1)%1.2,3)
        if t>=7.1:
            p=smooth((t-7.1)/2)
            height=173+(414-173)*p
            sprite=self.body(t,look,height)
            x=(270+263)*(1-p)+335*p;y=165*(1-p)+65*p
            im.paste(sprite,(round(x),round(y)),sprite)
            d=ImageDraw.Draw(im)
            if t>8.5:
                r=30+(t-8.5)*30
                d.ellipse((456-r,463-r*.14,456+r,463+r*.14),outline="#A793CE",width=2)
            text(d,(62,353),"Occasionally arrives\nby helicopter.",26,"#E9E5F7",True)


class ShowcaseWindow:
    def __init__(self, app, entrance_only=False):
        self.app=app;self.window=tk.Toplevel(app.root)
        self.window.title("Project Aura · Entrance & guided tour")
        self.window.configure(bg="#10151F")
        self.window.geometry("960x640")
        self.window.minsize(768,560)
        self.window.protocol("WM_DELETE_WINDOW",self.close)
        self.window.bind("<Escape>",lambda e:self.close())
        self.scene=Scene(app.store.read()["look"], app.inventory.selected(),app.store.read()["reduced_motion"])
        self.duration=12 if entrance_only else DURATION
        self.started=time.monotonic();self.elapsed=0;self.paused=False;self.job=None
        self.audio=Speech();self.sound=False
        self.canvas=tk.Canvas(self.window,bg="#10151F",highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        row=tk.Frame(self.window,bg="#10151F");row.pack(fill="x",padx=14,pady=8)
        self.pause_button=app.button(row,"Pause",self.toggle_pause);self.pause_button.pack(side="left",padx=4)
        app.button(row,"Replay",self.replay).pack(side="left",padx=4)
        self.sound_button=app.button(row,"Sound off",self.toggle_sound);self.sound_button.pack(side="left",padx=4)
        app.button(row,"Try this feature",self.try_feature,True).pack(side="right",padx=4)
        app.button(row,"Close tour",self.close).pack(side="right",padx=4)
        self.item=self.canvas.create_image(0,0,anchor="nw")
        self.tick()

    def restart_audio(self):
        self.audio.stop()
        if self.sound and not self.paused:
            path=ASSETS/"tour-audio.wav"
            if path.exists():
                # Load only the remaining PCM, allowing seek/resume without drift.
                import wave,tempfile
                with wave.open(str(path),"rb") as src:
                    src.setpos(min(src.getnframes(),round(self.elapsed*src.getframerate())))
                    params=src.getparams();data=src.readframes(src.getnframes())
                if data:
                    with tempfile.TemporaryDirectory(prefix="aura-tour-") as temp:
                        piece=Path(temp)/"part.wav"
                        with wave.open(str(piece),"wb") as dst:
                            dst.setparams(params);dst.writeframes(data)
                        self.audio.load(piece)

    def toggle_sound(self):
        self.sound=not self.sound
        self.sound_button.configure(text="Sound on" if self.sound else "Sound off")
        self.restart_audio()

    def toggle_pause(self):
        self.paused=not self.paused
        self.started=time.monotonic()-self.elapsed
        self.pause_button.configure(text="Resume" if self.paused else "Pause")
        self.restart_audio()

    def replay(self):
        self.elapsed=0;self.started=time.monotonic();self.paused=False
        self.pause_button.configure(text="Pause")
        self.restart_audio()

    def try_feature(self):
        index=chapter(self.elapsed)
        self.close()
        if index<=1:self.app.open_controls()
        elif index==2:self.app.tabs.select(self.app.look_page)
        elif index<=4:self.app.open_equipment()
        elif index==5:self.app.tabs.select(self.app.connect_page)
        else:self.app.open_equipment()
        self.app.root.deiconify();self.app.root.lift()

    def tick(self):
        if not self.window.winfo_exists():return
        start=time.monotonic()
        if not self.paused:self.elapsed=min(self.duration-.001,start-self.started)
        if start-self.started>=self.duration and not self.paused:
            self.paused=True;self.pause_button.configure(text="Resume");self.audio.stop()
        image=self.scene.frame(self.elapsed)
        w,h=max(1,self.canvas.winfo_width()),max(1,self.canvas.winfo_height())
        scale=min(w/WIDTH,h/HEIGHT)
        if w>10 and h>10:
            image=image.resize((max(1,round(WIDTH*scale)),max(1,round(HEIGHT*scale))),Image.Resampling.BILINEAR)
            self.photo=ImageTk.PhotoImage(image,master=self.canvas)
            self.canvas.itemconfigure(self.item,image=self.photo)
            self.canvas.coords(self.item,(w-image.width)/2,(h-image.height)/2)
        self.audio.poll()
        spent=round((time.monotonic()-start)*1000)
        self.job=self.window.after(max(16,(150 if self.paused or self.scene.reduced else 42)-spent),self.defer_tick)

    def defer_tick(self):
        self.job=self.window.after_idle(self.tick)

    def close(self):
        self.audio.stop()
        if self.job:
            try:self.window.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
        if self.window.winfo_exists():self.window.destroy()

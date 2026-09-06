"""Native desktop workbench and floating avatar. No network access in this module."""
from __future__ import annotations
import json
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from . import __version__
from .core import Store, AuraError, OPTIONS, INTERESTS, parse_request, validate_look
from .shell import Avatar, BG
from .bridge import launch
from .voice import Speech, MOODS
from .controls import Choice

PANEL, TEXT, MUTED, ACCENT = "#19212F", "#F0F1F8", "#A5B2C8", "#B6A0FF"


class App:
    def __init__(self, root, store):
        self.root, self.store = root, store
        root.tk.call("tk", "scaling", 4 / 3)
        self.preview = None
        from .equipment import Inventory
        self.inventory = Inventory(store.path.with_suffix(".equipment.json"))
        self.showcase = None
        from .tray import Preferences
        self.ui_preferences = Preferences(store.path.with_suffix(".ui.json"))
        self.tray = None
        self.instance = None
        self.lifecycle_job = None
        self.app_meter = None
        from .model_library import ModelLibrary
        self.model_library = ModelLibrary(store.path)
        self.model = self.model_library.restore()
        self.floating = None
        self.pending_ids = []
        self.poll_job = None
        self.voice_job = None
        self.demo_job = None
        self.speech = Speech()
        self.root.title("Project Aura " + __version__ + " · Studio")
        self.root.geometry("1120x800+30+30")
        self.root.minsize(1080, 800)
        self.root.configure(bg=BG)
        self.status = tk.StringVar(value="Ready. Start with a look, or share a few interests.")
        tk.Label(root, textvariable=self.status, bg="#171D2A", fg=TEXT, anchor="w", padx=22,
                 pady=12, wraplength=1020, font=("Segoe UI", 10)).pack(side="bottom", fill="x", pady=(8, 0))
        self.root.protocol("WM_DELETE_WINDOW", self.hide_studio)
        self.root.report_callback_exception = lambda typ, exc, tb: messagebox.showerror("Aura", str(exc), parent=root)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TNotebook.Tab", borderwidth=0)
        style.configure("TProgressbar", troughcolor="#20283A", background=ACCENT, borderwidth=0)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(11, 10), font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", "#2A3047")], foreground=[("selected", TEXT)])
        style.configure("TCombobox", fieldbackground="#273145", background="#273145", foreground=TEXT, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", "#273145")], foreground=[("readonly", TEXT)])
        self.label(root, "PROJECT AURA", size=12, color=ACCENT).pack(anchor="w", padx=30, pady=(22, 0))
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=30, pady=(5, 16))
        self.label(header, "Aura Studio", size=23, bold=True).pack(side="left")
        self.pause_btn = self.button(header, "Pause Aura", self.pause)
        self.pause_btn.pack(side="right")
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=24)
        left = tk.Frame(body, bg=BG, width=345)
        left.pack(side="left", fill="y", padx=(0, 24))
        left.pack_propagate(False)
        self.avatar = Avatar(left, store.read()["look"], width=340, height=330)
        self.avatar.pack(fill="both", expand=True)
        self.mode_label = self.label(left, "CURRENT APPEARANCE", size=10, color=ACCENT)
        self.mode_label.pack(pady=(0, 8))
        self.label(left, "Aura", size=22, bold=True).pack()
        self.label(left, "Drag her to a corner. Make it her own.", size=10, color=MUTED).pack(pady=(6, 14))
        self.button(left, "Use Aura preset", self.approved_look).pack(fill="x", pady=(0, 8))
        self.mouth_preview_btn = self.button(left, "Preview mouth movement", self.demo_speaking)
        self.mouth_preview_btn.pack(fill="x", pady=(0, 8))
        float_row = tk.Frame(left, bg=BG)
        float_row.pack(fill="x", pady=(0, 8))
        self.button(float_row, "Float on desktop", self.toggle_float).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.button(float_row, "Controls", self.open_controls).pack(side="left", fill="x", expand=True)

        self.button(left, "Entrance & guided tour", self.open_showcase).pack(fill="x", pady=(0, 8))
        self.root.bind_all("<Control-space>", lambda e: self.safe(self.open_controls))
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(side="left", fill="both", expand=True)
        self.look_page = self.page("Appearance")
        self.presence_page = self.page("Presence")
        self.gear_page = self.page("Equipment")
        self.prefs_page = self.page("Your interests")
        self.connect_page = self.page("Connection")
        self.model_page = self.page("Models")
        self.data_page = self.page("Your data")
        self.build_appearance()
        self.build_presence()
        self.build_equipment()
        self.build_preferences()
        self.build_connection()
        self.build_models()
        self.build_data()
        self.load_preferences()
        self.update_model_info()
        if self.model_library.warning:
            self.status.set(self.model_library.warning)
        self.sync_look()
        self.poll()
        self.voice_poll()

    def label(self, parent, text, size=11, color=TEXT, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), justify="left", anchor="w")

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=lambda: self.safe(command), bg=ACCENT if primary else "#293348",
                         fg="#131722" if primary else TEXT, activebackground="#C5B5FF", activeforeground="#131722",
                         relief="flat", bd=0, padx=14, pady=9, cursor="hand2", font=("Segoe UI", 10, "bold"))

    def safe(self, command):
        try:
            command()
        except (AuraError, OSError, sqlite3.Error, ValueError) as exc:
            self.status.set(str(exc))
            messagebox.showerror("Aura needs your attention", str(exc), parent=self.root)

    def page(self, title):
        page = tk.Frame(self.tabs, bg=PANEL, padx=22, pady=18)
        self.tabs.add(page, text=title)
        return page

    def paragraph(self, parent, text):
        widget = self.label(parent, text, size=10, color=MUTED)
        widget.configure(wraplength=490)
        widget.pack(anchor="w", pady=(5, 14))
        return widget

    def combo(self, parent, variable, choices):
        return Choice(parent, variable, choices)

    def check(self, parent, text, variable):
        w = tk.Checkbutton(parent, text=text, variable=variable, bg=PANEL, fg=TEXT,
                           selectcolor="#293348", activebackground=PANEL, activeforeground=TEXT,
                           font=("Segoe UI", 10), anchor="w", wraplength=470, justify="left")
        w.pack(anchor="w", pady=3)
        return w

    def build_appearance(self):
        p = self.look_page
        self.label(p, "Make her feel like Aura.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Choose a hairstyle, outfit and palette. Preview first; Apply saves your look. Illustrated faces and jewelry are fixed for now.")
        grid = tk.Frame(p, bg=PANEL)
        grid.pack(fill="x", pady=(0, 14))
        self.look_vars = {}
        self.look_boxes = {}
        self.look_labels = {}
        for i, (field, choices) in enumerate(OPTIONS.items()):
            label = self.label(grid, field.title())
            self.look_labels[field] = label
            label.grid(row=i, column=0, sticky="w", padx=(0, 24), pady=9)
            var = tk.StringVar(value=self.store.read()["look"][field])
            self.look_vars[field] = var
            box = self.combo(grid, var, choices)
            self.look_boxes[field] = box
            box.grid(row=i, column=1, sticky="ew", pady=9)
            box.bind("<<ComboboxSelected>>", lambda e: self.preview_controls())
        grid.columnconfigure(1, weight=1)
        self.label(p, "Or describe a look", size=11, bold=True).pack(anchor="w")
        self.request = tk.Entry(p, bg="#273145", fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 11))
        self.request.pack(fill="x", ipady=9, pady=(8, 6))
        self.request.insert(0, "ocean bob with headphones")
        self.request.bind("<Return>", lambda e: self.safe(self.preview_request))
        self.paragraph(p, "Quick requests use keywords such as violet, long, tactical, or stealth. For conversation and audio, open Presence.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.button(row, "Preview request", self.preview_request).pack(side="left", padx=(0, 8))
        self.button(row, "Apply look", self.apply_preview, True).pack(side="left")
        row2 = tk.Frame(p, bg=PANEL)
        row2.pack(fill="x", pady=(10, 0))
        self.button(row2, "Discard preview", self.discard).pack(side="left", padx=(0, 8))
        self.button(row2, "Undo last change", self.undo).pack(side="left")

    def approved_look(self):
        look = dict(self.store.read()["look"], outfit="tactical", hair="pixie", palette="violet", accessory="none")
        self.set_preview(look, "Approved design preview. Apply to save; choose stealth for Stealth Striker.")
        self.tabs.select(self.look_page)

    def demo_speaking(self):
        self.app_meter = None
        self.speech.stop()
        self.avatar.audio_level = None
        if self.avatar.paused or self.avatar.reduced:
            raise AuraError("Resume Aura and turn off Reduce motion to preview animation.")
        self.avatar.expression = "idle" if self.avatar.expression == "speaking" else "speaking"
        for avatar in self.avatars():
            avatar.expression = self.avatar.expression
            avatar.audio_level = None
            avatar.wake()
        if self.demo_job:
            self.root.after_cancel(self.demo_job)
            self.demo_job = None
        active = self.avatar.expression == "speaking"
        self.mouth_preview_btn.configure(text="Stop mouth preview" if active else "Preview mouth movement")
        if active:
            self.demo_job = self.root.after(4000, self.end_demo)
        self.status.set("Local mouth animation preview; no audio or GPT Voice synchronization." if self.avatar.expression == "speaking" else "Idle animation resumed.")

    def end_demo(self):
        if self.demo_job:
            self.root.after_cancel(self.demo_job)
        self.demo_job = None
        for avatar in self.avatars():
            avatar.expression = "idle"
        self.mouth_preview_btn.configure(text="Preview mouth movement")

    def set_preview(self, look, reason):
        self.preview = validate_look(look)
        self.update_body_controls(look)
        self.avatar.look = look.copy()
        for k, v in look.items():
            self.look_vars[k].set(v)
        self.mode_label.configure(text="PREVIEW · NOT YET APPLIED")
        self.status.set(reason)

    def update_body_controls(self, look):
        for field in ("accessory", "silhouette"):
            illustrated = look["outfit"] in ("tactical", "stealth")
            self.look_boxes[field].configure(state="disabled" if illustrated else "readonly")
            for widget in (self.look_boxes[field], self.look_labels[field]):
                widget.grid_remove() if illustrated else widget.grid()

    def preview_controls(self):
        self.set_preview({k: v.get() for k, v in self.look_vars.items()}, "Preview only. Apply look when you are ready.")

    def preview_request(self):
        patch = parse_request(self.request.get())
        self.set_preview(dict(self.store.read()["look"], **patch), "Request matched locally. Review the preview, then Apply look.")

    def apply_preview(self):
        if self.preview is None:
            raise AuraError("Preview a change first.")
        self.store.apply(self.preview)
        self.preview = None
        self.sync_look()
        self.status.set("New appearance saved. You can undo the last 20 changes.")

    def discard(self):
        self.preview = None
        self.sync_look()
        self.status.set("Preview discarded. Your saved appearance is unchanged.")

    def undo(self):
        self.store.undo()
        self.preview = None
        self.sync_look()
        self.status.set("Previous appearance restored.")

    def scrollable_content(self, host):
        viewport = tk.Canvas(host, bg=PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=viewport.yview)
        scrollbar.pack(side="right", fill="y")
        viewport.pack(side="left", fill="both", expand=True)
        viewport.configure(yscrollcommand=scrollbar.set)
        p = tk.Frame(viewport, bg=PANEL)
        window = viewport.create_window((0, 0), window=p, anchor="nw")
        p.bind("<Configure>", lambda event: viewport.configure(scrollregion=viewport.bbox("all")))
        viewport.bind("<Configure>", lambda event: viewport.itemconfigure(window, width=event.width))
        return p

    def build_presence(self):
        p = self.scrollable_content(self.presence_page)
        self.label(p, "Voice & expression", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Local speech, a chosen WAV, or experimental app-level metering. Mouth movement follows loudness; no microphone or transcript access.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.mood = tk.StringVar(value="neutral")
        self.effect = tk.StringVar(value="solid")
        self.label(row, "Mood").grid(row=0, column=0, sticky="w", padx=(0, 12))
        box = self.combo(row, self.mood, MOODS)
        box.grid(row=0, column=1, pady=3)
        box.bind("<<ComboboxSelected>>", lambda e: self.apply_presence())
        self.label(row, "Rendering").grid(row=1, column=0, sticky="w", padx=(0, 12))
        box = self.combo(row, self.effect, ("solid", "hologram"))
        box.grid(row=1, column=1, pady=3)
        box.bind("<<ComboboxSelected>>", lambda e: self.apply_presence())
        self.paragraph(p, "Mood and rendering are session choices.")
        self.speech_text = tk.Text(p, height=3, bg="#273145", fg=TEXT, insertbackground=TEXT,
                                   relief="flat", wrap="word", font=("Segoe UI", 11))
        self.speech_text.pack(fill="x", pady=(0, 8))
        self.speech_text.insert("1.0", "Hey Alex. Aura here. My voice and my mouth are finally working together.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.voice = tk.StringVar(value="default")
        self.combo(row, self.voice, ("default", "female", "male")).pack(side="left", padx=(0, 8))
        self.button(row, "Speak text", self.speak_text, True).pack(side="left", padx=(0, 8))
        self.button(row, "Stop", self.stop_speech).pack(side="left")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", pady=8)
        self.button(row, "Play a WAV…", self.play_wav).pack(side="left", padx=(0, 12))
        self.voice_state = self.label(row, "Silent", size=10, color=ACCENT)
        self.voice_state.pack(side="left")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.label(row, "Mouth delay (ms)", size=10).pack(side="left")
        self.delay = tk.IntVar(value=0)
        tk.Scale(row, from_=-300, to=300, resolution=25, variable=self.delay, orient="horizontal",
                 bg=PANEL, fg=TEXT, highlightthickness=0, length=180).pack(side="left", padx=8)
        self.level = ttk.Progressbar(row, maximum=1, length=70)
        self.level.pack(side="left", padx=8)
        self.paragraph(p, "WAV: 16-bit PCM, up to two minutes.")
        audio_row = tk.Frame(p, bg=PANEL); audio_row.pack(fill="x", pady=4)
        self.audio_apps = ttk.Combobox(audio_row, state="readonly", width=25)
        self.audio_apps.pack(side="left", padx=(0, 6))
        self.audio_sessions = []
        self.button(audio_row, "Refresh", self.refresh_audio_apps).pack(side="left")
        self.button(audio_row, "Follow app", self.follow_audio_app).pack(side="left", padx=6)
        self.paragraph(p, "Experimental: start app audio, Refresh, select its session, then Follow app. Stop disconnects. Notifications also move the mouth; words and emotion are unavailable.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.button(row, "Dock left", lambda: self.dock_avatar("left")).pack(side="left", padx=(0, 8))
        self.button(row, "Dock right", lambda: self.dock_avatar("right")).pack(side="left", padx=(0, 8))
        self.button(row, "Play entrance", self.entrance).pack(side="left")

    def refresh_audio_apps(self):
        from .app_audio import sessions
        self.audio_sessions = sessions()
        self.audio_apps.configure(values=[row[0] for row in self.audio_sessions])
        self.audio_apps.set("")
        self.status.set("Choose the app audio session you want Aura to follow. Metering is off until Follow app.")

    def follow_audio_app(self):
        if self.store.read()["paused"]:
            raise AuraError("Resume Aura before following audio.")
        index = self.audio_apps.current()
        if index < 0:
            raise AuraError("Refresh and choose an active app audio session first.")
        from .app_audio import AppMeter
        _, session, created = self.audio_sessions[index]
        self.stop_speech()
        self.app_meter = AppMeter(session, created)
        self.status.set("Following " + self.app_meter.name + " audio level only. No recording or transcription. Stop disconnects.")

    def apply_presence(self):
        for avatar in self.avatars():
            avatar.mood, avatar.effect = self.mood.get(), self.effect.get()

    def avatars(self):
        result = [self.avatar]
        if self.floating and self.floating.winfo_exists():
            result.append(self.float_avatar)
        return result

    def speak_text(self):
        self.app_meter = None
        self.end_demo()
        if self.store.read()["paused"]:
            raise AuraError("Resume Aura before speaking.")
        rate = {"neutral": 0, "happy": 1, "thoughtful": -1, "focused": 0, "sleepy": -2}[self.mood.get()]
        self.speech.speak(self.speech_text.get("1.0", "end-1c"), self.voice.get(), rate)
        for avatar in self.avatars():
            avatar.expression, avatar.audio_level = "idle", 0
        self.status.set("Preparing speech locally with Windows. No text is sent to a service.")

    def perform(self, payload):
        if "cue" in payload:
            from .core import validate_cue
            cue = validate_cue(payload)["cue"]
            if cue == "entrance":
                self.entrance()
            elif cue == "cast":
                self.cast_spell()
            elif cue in ("wave", "inspect", "draw"):
                self.play_model_motion(cue)
            else:
                self.require_effects()
                if "holster" not in self.inventory.equipped:
                    raise AuraError("Equip a holster item before revealing or stowing it.")
                if self.model:
                    raise AuraError("This rig supports the draw cycle. Request draw instead of persistent reveal/stow.")
                for avatar in self.avatars():
                    avatar.item_revealed = cue == "reveal"
            return "Visual cue started locally; completion is not confirmed."
        from .core import validate_performance
        payload = validate_performance(payload)
        self.mood.set(payload["mood"])
        self.apply_presence()
        if payload["text"].strip():
            self.speech_text.delete("1.0", "end")
            self.speech_text.insert("1.0", payload["text"])
            self.speak_text()
            self.tabs.select(self.presence_page)
            return "Mood set and local speech preparation started; playback completion is not confirmed."
        return "Session mood applied."

    def play_wav(self):
        if self.store.read()["paused"]:
            raise AuraError("Resume Aura before playing audio.")
        path = filedialog.askopenfilename(parent=self.root, title="Choose audio for Aura", filetypes=[("PCM WAV", "*.wav")])
        if path:
            self.stop_speech()
            self.speech.load(path)
            for avatar in self.avatars():
                avatar.expression, avatar.audio_level = "idle", 0
            self.status.set("Playing the selected WAV locally; mouth movement follows its loudness.")

    def stop_speech(self):
        self.app_meter = None
        self.end_demo()
        self.speech.stop()
        for avatar in self.avatars():
            avatar.expression, avatar.audio_level = "idle", None
        self.status.set("Speech stopped.")

    def voice_poll(self):
        try:
            self.speech.delay_ms = self.delay.get()
            level = self.app_meter.level() if self.app_meter else self.speech.poll()
            active = self.app_meter is not None or self.speech.state != "idle"
            for avatar in self.avatars():
                avatar.audio_level = level if active else None
            self.level["value"] = level
            self.voice_state.configure(text=("Following " + self.app_meter.name) if self.app_meter else {"idle": "Silent", "preparing": "Preparing…", "playing": "Speaking / playing"}[self.speech.state])
        except (AuraError, OSError, RuntimeError) as exc:
            self.stop_speech()
            self.voice_state.configure(text="Audio unavailable")
            self.status.set(str(exc))
        self.voice_job = self.root.after(25, self.voice_poll)

    def dock_avatar(self, side):
        if not self.floating or not self.floating.winfo_exists():
            self.toggle_float()
        from .presence import dock
        dock(self.floating, side)
        self.status.set("Aura docked to the " + side + " of her current monitor.")

    def entrance(self):
        if self.avatar.paused or self.avatar.reduced:
            raise AuraError("Resume Aura and turn off Reduce motion to play an entrance.")
        for avatar in self.avatars():
            avatar.arrival = avatar.tick
        self.open_showcase(entrance_only=True)

    def open_controls(self):
        if not self.floating or not self.floating.winfo_exists():
            self.toggle_float()
        self.control_wheel.toggle()
        self.floating.lift()

    def open_equipment(self):
        self.root.deiconify()
        self.root.lift()
        self.tabs.select(self.gear_page)

    def open_showcase(self, entrance_only=False):
        if self.store.read()["paused"]:
            raise AuraError("Resume Aura before opening the tour.")
        if self.showcase and self.showcase.window.winfo_exists():
            self.showcase.window.lift()
            return
        from .showcase import ShowcaseWindow
        self.stop_speech()
        self.showcase = ShowcaseWindow(self, entrance_only)
        self.status.set("Playing the local Aura stage. Escape closes it; the tour previews do not change your saved look.")

    def build_models(self):
        p=self.scrollable_content(self.model_page)
        self.label(p,"Models & shared animation",size=17,bold=True).pack(anchor="w")
        self.paragraph(p,"Aura Rig 1 accepts original PNG layers on named joints. Compatible bodies share idle, inspect, wave and draw motions. It does not yet import VRM, Live2D or arbitrary 3D files.")
        self.model_info=self.label(p,"Default illustrated / classic body",size=11,color=ACCENT)
        self.model_info.configure(wraplength=470);self.model_info.pack(anchor="w",pady=10)
        self.model_list=tk.Listbox(p,height=4,bg="#202A3D",fg=TEXT,selectbackground="#655493",
                                   relief="flat",exportselection=False,font=("Segoe UI",10))
        self.model_list.pack(fill="x",pady=5)
        self.model_list.bind("<Double-Button-1>",lambda e:self.safe(self.choose_library_model))
        self.model_list.bind("<Return>",lambda e:self.safe(self.choose_library_model))
        self.refresh_model_library()
        row=tk.Frame(p,bg=PANEL);row.pack(fill="x")
        self.button(row,"Use selected model",self.choose_library_model).pack(side="left",padx=(0,8))
        self.button(row,"Import model.json…",self.import_model).pack(side="left")
        self.button(p,"Open reference rig",self.use_reference_model).pack(anchor="w",pady=5)
        self.button(p,"Restore default Aura",self.clear_model).pack(anchor="w",pady=5)
        row=tk.Frame(p,bg=PANEL);row.pack(fill="x",pady=12)
        for motion in ("wave","inspect","draw"):
            self.button(row,motion.title(),lambda m=motion:self.play_model_motion(m)).pack(side="left",padx=(0,8))
        self.paragraph(p,"The reference rig is a technical mannequin, not a replacement for Aura's approved artwork. Draw requires a holster item. Imported packs and your selection are saved locally. Restart restores your model; missing or damaged packs fall back to default Aura.")
        self.paragraph(p,"Compatibility depends on declared joints and sockets. Missing optional joints disable those motions; extra joints and custom art remain allowed. See docs/model-standard.md and the reference pack for authoring.")

    def refresh_model_library(self):
        self.model_entries=self.model_library.entries()
        self.model_list.delete(0,tk.END)
        for index,(key,label) in enumerate(self.model_entries):
            self.model_list.insert(tk.END,label)
            if key==self.model_library.selected:
                self.model_list.selection_set(index)
                self.model_list.see(index)

    def update_model_info(self):
        model=self.model
        self.model_info.configure(text=(model.data["name"]+" · "+model.data["author"]+" · "+model.data["license"]+
            "\nMotions: "+", ".join(model.capabilities)) if model else "Default illustrated / classic body")

    def set_model(self,model):
        self.model=model
        for surface in self.avatars():
            surface.model_motion='idle'
            surface.model_motion_started=-100
        self.update_model_info()
        self.refresh_model_library()
        self.sync_look()

    def choose_library_model(self):
        selection=self.model_list.curselection()
        if not selection:raise AuraError("Select a model in the library first.")
        key,_=self.model_entries[selection[0]]
        self.set_model(self.model_library.choose(key))
        self.status.set("Model selected and saved for next launch.")

    def import_model(self):
        path=filedialog.askopenfilename(parent=self.root,title="Choose Aura Rig 1 model",filetypes=[("Model manifest","*.json")])
        if path:
            _,model=self.model_library.import_model(path)
            self.set_model(model)
            self.status.set("Model validated, copied to your library and saved for next launch.")

    def use_reference_model(self):
        self.set_model(self.model_library.choose('@reference'))
        self.status.set("Reference rig saved. Try Wave, Inspect, or equip a dagger and Draw.")

    def clear_model(self):
        self.set_model(self.model_library.choose(None))

    def play_model_motion(self,motion):
        if not self.model:raise AuraError("Choose a rigged model first.")
        if self.avatar.paused or self.avatar.reduced:raise AuraError("Resume Aura and disable Reduce motion first.")
        if motion not in self.model.capabilities:raise AuraError("This model does not declare the joints/sockets for that motion.")
        if motion=="draw" and "holster" not in self.inventory.equipped:raise AuraError("Equip a holster item before Draw.")
        for surface in self.avatars():
            surface.model_motion=motion;surface.model_motion_started=surface.motion.time
        self.status.set("Playing shared rig motion: "+motion)

    def build_equipment(self):
        p = self.gear_page
        self.label(p, "Equipment & spellbook", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Equip a holster item, satchel, charm and visual spell. Items appear on the illustrated Tactical Ops and Stealth Striker bodies. Apparel is changed in Appearance.")
        self.gear_list = tk.Listbox(p, height=8, bg="#202A3D", fg=TEXT, selectbackground="#655493",
                                   relief="flat", font=("Segoe UI", 11), exportselection=False)
        self.gear_list.pack(fill="x")
        self.gear_list.bind("<<ListboxSelect>>", lambda e: self.describe_equipment())
        self.gear_details = self.label(p, "", size=10, color=MUTED)
        self.gear_details.configure(wraplength=480)
        self.gear_details.pack(anchor="w", pady=10)
        row = tk.Frame(p, bg=PANEL); row.pack(fill="x")
        self.button(row, "Equip / remove", self.equip_selected, True).pack(side="left", padx=(0,8))
        self.button(row, "Undo", self.undo_equipment).pack(side="left")
        row = tk.Frame(p, bg=PANEL); row.pack(fill="x", pady=10)
        self.button(row, "Reveal / stow", self.reveal_equipment).pack(side="left", padx=(0,8))
        self.button(row, "Cast spell", self.cast_spell).pack(side="left")
        self.button(p, "Import creator item…", self.import_equipment).pack(anchor="w", pady=8)
        self.paragraph(p, "Creator items are small JSON files: name, type, color and attribution. This first format uses Aura's built-in prop shapes; custom meshes, image assets and new body rigs are not yet supported. Visual spells never run commands.")
        self.refresh_equipment()

    def refresh_equipment(self):
        self.gear_list.delete(0, "end")
        for item in self.inventory.items:
            mark = "Equipped" if self.inventory.equipped.get(item["slot"]) == item["id"] else item["slot"].title()
            self.gear_list.insert("end", item["name"] + "  ·  " + mark)
        for avatar in self.avatars():
            avatar.equipment = self.inventory.selected()
        self.gear_details.configure(text="Select an item to see its creator and license.")

    def selected_equipment(self):
        selection = self.gear_list.curselection()
        if not selection:
            raise AuraError("Select an equipment item first.")
        return self.inventory.items[selection[0]]

    def describe_equipment(self):
        if self.gear_list.curselection():
            item = self.selected_equipment()
            self.gear_details.configure(text=f'{item["name"]} · {item["author"]} · {item["license"]}')

    def equip_selected(self):
        item = self.selected_equipment()
        self.inventory.equip(item["id"])
        self.refresh_equipment()
        self.status.set("Equipment saved. Use an illustrated body to see its attachments.")

    def undo_equipment(self):
        self.inventory.undo()
        self.refresh_equipment()
        self.status.set("Equipment change undone.")

    def reveal_equipment(self):
        self.require_effects()
        if "holster" not in self.inventory.equipped:
            raise AuraError("Equip Hidden dagger or another holster item first.")
        if self.model:
            self.play_model_motion("draw")
            return
        for avatar in self.avatars():
            avatar.item_revealed = not getattr(avatar, "item_revealed", False)
        self.status.set("Playing the dagger's floating reveal / stow. Hand-grip animation needs a layered body rig.")

    def require_effects(self):
        if self.avatar.paused or self.avatar.reduced:
            raise AuraError("Resume Aura and disable Reduce motion to play an effect.")
        if self.model is None and self.store.read()["look"]["outfit"] not in ("tactical", "stealth"):
            raise AuraError("Select Tactical Ops or Stealth Striker in Appearance for equipment effects.")

    def cast_spell(self):
        self.require_effects()
        if "spell" not in self.inventory.equipped:
            raise AuraError("Equip a spell first.")
        for avatar in self.avatars():
            avatar.cast_started = avatar.motion.time
        self.status.set("Casting a local visual spell. No application or file is affected.")

    def import_equipment(self):
        path = filedialog.askopenfilename(parent=self.root, title="Import Aura creator item", filetypes=[("Aura item JSON", "*.json")])
        if path:
            item = self.inventory.import_item(path)
            self.refresh_equipment()
            self.status.set("Imported " + item["name"] + ". Select it and equip when ready.")

    def build_preferences(self):
        p = self.prefs_page
        self.label(p, "A little more like your world.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Choose what you want Aura to know. She never watches your browsing, apps or conversations to infer habits.")
        self.interest_vars = {}
        grid = tk.Frame(p, bg=PANEL)
        grid.pack(fill="x")
        for i, interest in enumerate(INTERESTS):
            var = tk.BooleanVar()
            self.interest_vars[interest] = var
            w = tk.Checkbutton(grid, text=interest.title(), variable=var, bg=PANEL, fg=TEXT, selectcolor="#293348",
                               activebackground=PANEL, activeforeground=TEXT, font=("Segoe UI", 11))
            w.grid(row=i//3, column=i%3, sticky="w", padx=(0, 20), pady=4)
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", pady=12)
        self.label(row, "Favorite palette").pack(side="left", padx=(0, 20))
        self.favorite = tk.StringVar()
        self.combo(row, self.favorite, OPTIONS["palette"]).pack(side="left")
        self.adapt = tk.BooleanVar()
        self.reduced = tk.BooleanVar()
        self.check(p, "Adapt automatically when I record an activity", self.adapt)
        self.check(p, "Reduce motion", self.reduced)
        self.paragraph(p, "Automatic adaptation uses only saved interests and activity counts you enter here. It can change outfit, accessory and palette. Every change can be undone.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", pady=(0, 18))
        self.button(row, "Save preferences", self.save_preferences, True).pack(side="left", padx=(0, 8))
        self.button(row, "Suggest from interests", self.suggest).pack(side="left")
        self.label(p, "What have you been enjoying?", bold=True).pack(anchor="w")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x", pady=10)
        self.activity = tk.StringVar(value="making")
        self.combo(row, self.activity, INTERESTS).pack(side="left", padx=(0, 10))
        self.button(row, "Record activity", self.record).pack(side="left")
        self.count_label = self.paragraph(p, "No activities recorded.")

    def load_preferences(self):
        state = self.store.read()
        for key, var in self.interest_vars.items():
            var.set(key in state["interests"])
        self.favorite.set(state["favorite"])
        self.adapt.set(state["adapt"])
        self.reduced.set(state["reduced_motion"])
        self.bridge_var.set(state["bridge"])
        self.share_var.set(state["share"])

    def save_preferences(self):
        self.store.preferences([k for k, v in self.interest_vars.items() if v.get()], self.favorite.get(), self.adapt.get(),
                               self.bridge_var.get(), self.share_var.get(), self.reduced.get())
        self.sync_look()
        self.status.set("Preferences saved locally.")

    def suggest(self):
        look, reason = self.store.suggestion()
        self.set_preview(look, reason)
        self.tabs.select(self.look_page)

    def record(self):
        result = self.store.record_activity(self.activity.get())
        self.preview = None
        self.sync_look()
        self.status.set(result)

    def build_connection(self):
        p = self.connect_page
        self.label(p, "Bring ChatGPT into the loop.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Your MCP connection lets ChatGPT propose looks, speech with a mood, visual cues, or opening Notepad. You approve each request here. Enabling this switch alone does not connect your account.")
        self.bridge_var, self.share_var = tk.BooleanVar(), tk.BooleanVar()
        self.check(p, "Allow requests from my connected MCP client", self.bridge_var)
        self.check(p, "Also share my interests and favorite palette", self.share_var)
        self.button(p, "Save connection settings", self.save_preferences, True).pack(anchor="w", pady=8)
        self.paragraph(p, "Use a compatible local MCP client with stdio. Copy this build's setup below. No ChatGPT password or API key is needed by Aura; built-in GPT Voice audio is not connected.")
        self.button(p, "Copy MCP setup", self.copy_mcp_setup).pack(anchor="w", pady=(0, 10))
        self.label(p, "Requests waiting for you", bold=True).pack(anchor="w", pady=(0, 8))
        self.requests = tk.Listbox(p, height=4, bg="#111824", fg=TEXT, selectbackground="#594984",
                                   selectforeground=TEXT, relief="flat", highlightthickness=0, font=("Segoe UI", 10))
        self.requests.pack(fill="x", pady=(0, 10))
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.button(row, "Review selected", self.review).pack(side="left", padx=(0, 8))
        self.button(row, "Reject selected", self.reject).pack(side="left")
        self.button(p, "Open Notepad · local demo", self.local_launch).pack(anchor="w", pady=14)
        self.label(p, "Requests expire after 10 minutes. Pause cancels pending requests.", size=9, color=MUTED).pack(anchor="w")

    def copy_mcp_setup(self):
        import sys
        if getattr(sys, "frozen", False):
            command = str(Path(sys.executable).parent / "bridge" / "AuraMCP.exe")
            args = ["--data", str(self.store.path.resolve())]
        else:
            command = sys.executable
            args = [str(Path(__file__).resolve().parents[1] / "run_aura.py"), "--mcp", "--data", str(self.store.path.resolve())]
        config = json.dumps({"mcpServers": {"project-aura": {"command": command, "args": args}}}, indent=2)
        self.root.clipboard_clear()
        self.root.clipboard_append(config)
        self.status.set("Copied this profile's stdio command and arguments. Paste into your MCP client's configuration; restart its Aura connection to refresh tools.")

    def selected_request(self):
        selection = self.requests.curselection()
        if not selection:
            raise AuraError("Select a pending request first.")
        return self.pending_ids[selection[0]]

    def confirm_performance(self, payload):
        dialog = tk.Toplevel(self.root)
        dialog.title("Review Aura speech request")
        dialog.geometry("560x400")
        dialog.minsize(480, 320)
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        self.label(dialog, "Mood: " + payload["mood"], bold=True).pack(anchor="w", padx=18, pady=12)
        self.label(dialog, "The text below will be spoken with a local Windows voice.", size=10).pack(anchor="w", padx=18)
        body = tk.Frame(dialog, bg=PANEL)
        body.pack(fill="both", expand=True, padx=18, pady=12)
        text = tk.Text(body, wrap="word", bg=BG, fg=TEXT, font=("Segoe UI", 11))
        scroll = ttk.Scrollbar(body, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.insert("1.0", payload["text"] or "Mood only — no speech.")
        text.configure(state="disabled")
        accepted = []
        def approve():
            accepted.append(True)
            dialog.destroy()
        row = tk.Frame(dialog, bg=PANEL)
        row.pack(fill="x", padx=18, pady=(0, 14))
        self.button(row, "Approve", approve, True).pack(side="left", padx=(0, 8))
        self.button(row, "Cancel", dialog.destroy).pack(side="left")
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.grab_set()
        self.root.wait_window(dialog)
        return bool(accepted)

    def review(self):
        request_id = self.selected_request()
        row = next((r for r in self.store.pending() if r["id"] == request_id), None)
        if row is None:
            raise AuraError("Request expired or was already reviewed.")
        payload = json.loads(row["payload"])
        detail = "Open Windows Notepad?" if row["kind"] == "launch" else "Apply these avatar changes?\n\n" + "\n".join(f"{k.title()}: {v}" for k,v in payload.items())
        if row["kind"] == "cue":
            detail = "Play this local visual cue?\n\n" + payload["cue"].title() + "\n\nNo files or apps will be changed."
        if row["kind"] == "performance":
            detail = "Use a local Windows voice to speak this text?\nMood: " + payload["mood"] + "\n\n" + (payload["text"] or "(Mood only; no speech)")
        if row["kind"] == "appearance":
            self.set_preview(dict(self.store.read()["look"], **payload), "Reviewing an MCP appearance proposal.")
            self.root.update_idletasks()
        accepted = self.confirm_performance(payload) if row["kind"] == "performance" else messagebox.askyesno("Review request from connected client", detail, parent=self.root)
        if accepted:
            self.status.set(self.store.resolve(request_id, True, launch, self.perform))
            self.preview = None
            self.sync_look()
        else:
            self.preview = None
            self.sync_look()
            self.status.set("Request left pending. Reject it or review again later.")
        self.refresh_requests()

    def reject(self):
        self.status.set(self.store.resolve(self.selected_request(), False, launch))
        self.refresh_requests()

    def local_launch(self):
        if self.store.read()["paused"]:
            raise AuraError("Resume Aura first.")
        if messagebox.askyesno("Open Notepad", "Allow Aura to open Windows Notepad? No text or commands will be entered.", parent=self.root):
            self.status.set(launch("notepad"))
            if not self.avatar.reduced:
                for avatar in self.avatars():
                    avatar.arrival = avatar.tick

    def build_data(self):
        p = self.data_page
        self.label(p, "Your preferences, your control.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Aura stores appearance, up to 20 previous looks, selected interests, activity counts, settings and up to 100 request records (including proposed speech text) on this computer. There is no telemetry, microphone recording or screen capture.")
        self.paragraph(p, "Data is not encrypted. Other programs running as you may read it. Sharing through MCP is off by default; when enabled, tool inputs and results may be processed by your connected provider.")
        self.button(p, "Export my preferences", self.export).pack(anchor="w", pady=(0, 10))
        self.button(p, "Forget my data and reset Aura", self.forget).pack(anchor="w", pady=(0, 16))
        self.paragraph(p, "Reset clears Aura's local preferences, history and request records, and disables the connection. Imported model artwork, tray visibility, exports, backups and information shared with another service are retained.")
        self.label(p, "Beta " + __version__, color=ACCENT, bold=True).pack(anchor="w", pady=(12, 0))
        self.paragraph(p, "This beta includes an illustrated sprite body and a classic procedural avatar. It does not edit AI model weights, generate 3D meshes, control games, or design machine parts. Project Aura is independent of OpenAI.")
        path = self.paragraph(p, "Local data: " + str(self.store.path))
        path.configure(wraplength=490)

    def export(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="Export Aura data", defaultextension=".json", initialfile="aura-preferences.json", filetypes=[("JSON", "*.json")])
        if path:
            if Path(path).resolve() in (self.store.path.resolve(), self.inventory.path.resolve(), self.ui_preferences.path.resolve(), self.model_library.settings.resolve()):
                raise AuraError("Choose an export filename different from Aura's database.")
            Path(path).write_text(json.dumps({"schema": 1, "preferences": self.store.read(), "equipment": {"items": self.inventory.custom, "equipped": self.inventory.equipped}}, indent=2), encoding="utf-8")
            self.status.set("Preferences exported. Keep the file private if it contains personal interests.")

    def forget(self):
        if messagebox.askyesno("Reset Aura", "Clear local preferences, appearance history and queued requests? This cannot be undone.", parent=self.root):
            self.stop_speech()
            self.speech_text.delete("1.0", "end")
            self.store.forget()
            self.clear_model()
            self.inventory.reset()
            self.refresh_equipment()
            self.preview = None
            self.load_preferences()
            self.sync_look()
            self.refresh_requests()
            self.status.set("Local data reset. Connection disabled.")

    def pause(self):
        self.end_demo()
        self.stop_speech()
        self.store.set_paused(not self.store.read()["paused"])
        self.preview = None
        self.sync_look()
        self.refresh_requests()
        self.status.set("Paused; pending requests cancelled." if self.store.read()["paused"] else "Aura resumed.")

    def sync_look(self):
        state = self.store.read()
        if self.preview is None:
            self.avatar.look = state["look"].copy()
            self.update_body_controls(state["look"])
            for key, var in self.look_vars.items():
                var.set(state["look"][key])
            self.mode_label.configure(text="PAUSED" if state["paused"] else "CURRENT APPEARANCE")
        for surface in self.avatars():
            surface.equipment = self.inventory.selected()
            surface.model = self.model
        if self.showcase and self.showcase.window.winfo_exists():
            self.showcase.scene.reduced = state["reduced_motion"]
        if self.showcase and self.showcase.window.winfo_exists() and state["paused"]:
            self.showcase.close()
        self.avatar.reduced = state["reduced_motion"]
        self.avatar.paused = state["paused"]
        if state["paused"] and (self.app_meter is not None or self.speech.state != "idle"):
            self.stop_speech()
        self.pause_btn.configure(text="Resume Aura" if state["paused"] else "Pause Aura")
        self.count_label.configure(text="Recorded activities: " + (", ".join(f"{k} {v}" for k,v in state["habits"].items()) or "none"))
        if self.floating and self.floating.winfo_exists():
            self.float_avatar.look = state["look"].copy()
            self.float_avatar.reduced = state["reduced_motion"]
            self.float_avatar.paused = state["paused"]

    def toggle_float(self):
        if self.floating and self.floating.winfo_exists():
            self.floating.destroy()
            self.floating = None
            if self.tray and not self.tray.visible:
                self.show_studio()
            return
        window = tk.Toplevel(self.root)
        window.withdraw()
        self.floating = window
        window.title("Aura · drag to move")
        window.geometry("280x540+60+90")
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.configure(bg=BG)
        if os.name == "nt":
            window.attributes("-transparentcolor", BG)
        self.float_avatar = Avatar(window, self.store.read()["look"], width=245, height=285)
        self.float_avatar.desktop_mode = True
        self.float_avatar.expression = self.avatar.expression
        self.float_avatar.audio_level = self.avatar.audio_level
        self.float_avatar.mood, self.float_avatar.effect = self.mood.get(), self.effect.get()
        self.float_avatar.pack(fill="both", expand=True)
        self.float_avatar.bind("<ButtonPress-1>", lambda e: setattr(self, "drag", (e.x_root-window.winfo_x(), e.y_root-window.winfo_y())))
        from .presence import move
        self.float_avatar.bind("<B1-Motion>", lambda e: move(window, e.x_root-self.drag[0], e.y_root-self.drag[1]) if hasattr(self, "drag") and not self.control_wheel.key else None)
        self.float_avatar.bind("<Double-Button-1>", lambda e: self.safe(self.entrance))
        menu = tk.Menu(window, tearoff=False, bg=PANEL, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        menu.add_command(label="Open Aura Studio", command=self.show_studio)
        menu.add_command(label="More / tray settings", command=self.open_menu)
        menu.add_command(label="Show controls", command=self.open_controls)
        menu.add_command(label="Equipment", command=self.open_equipment)
        menu.add_command(label="Play entrance", command=lambda: self.safe(self.entrance))
        menu.add_separator()
        menu.add_command(label="Larger", command=lambda: self.resize_float(1.15))
        menu.add_command(label="Smaller", command=lambda: self.resize_float(1 / 1.15))
        menu.add_command(label="Dock left", command=lambda: self.dock_avatar("left"))
        menu.add_command(label="Dock right", command=lambda: self.dock_avatar("right"))
        menu.add_separator()
        menu.add_command(label="Pause / resume", command=lambda: self.safe(self.pause))
        menu.add_command(label="Hide Aura", command=self.toggle_float)
        self.float_avatar.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        window.bind("<Escape>", lambda e: self.toggle_float())
        self.sync_look()
        window.deiconify()
        window.update_idletasks()
        window.lift()
        self.float_avatar.wake()
        from .wheel import ControlWheel
        def open_page(page):
            self.root.deiconify()
            self.root.lift()
            self.tabs.select(page)
        self.control_wheel = ControlWheel(self.float_avatar, [
            ("Look", lambda: open_page(self.look_page)),
            ("Voice", lambda: open_page(self.presence_page)),
            ("Gear", self.open_equipment),
            ("Hide", self.toggle_float),
            ("Pause", lambda: self.safe(self.pause)),
            ("Menu", self.open_menu),
        ])
        self.float_handle = tk.Button(window, text="Controls", command=self.open_controls,
            bg="#293348", fg=TEXT, activebackground=ACCENT, relief="flat", cursor="hand2",
            font=("Segoe UI", 9, "bold"), takefocus=True)
        self.float_handle.place(relx=1, x=-8, y=8, anchor="ne")
        self.status.set("Click Controls beside Aura, or use Aura controls in Studio. Ctrl+Space works while Aura has focus; Shift-hover is optional.")

    def resize_float(self, factor):
        if self.floating and self.floating.winfo_exists():
            height = max(280, min(760, round(self.floating.winfo_height() * factor)))
            width = round(height * .52)
            self.floating.geometry(f"{width}x{height}")

    def refresh_requests(self):
        pending = self.store.pending()
        ids = [r["id"] for r in pending]
        if ids != self.pending_ids:
            new_requests = set(ids) - set(self.pending_ids)
            if new_requests and self.root.state() == "withdrawn":
                self.show_studio()
                self.tabs.select(self.connect_page)
            self.requests.delete(0, "end")
            for row in pending:
                payload = json.loads(row["payload"])
                text = "Open Notepad" if row["kind"] == "launch" else "Appearance: " + ", ".join(payload.values())
                if row["kind"] == "performance":
                    text = "Speech / " + payload["mood"] + ": " + (payload["text"][:60].replace("\n", " ") or "mood only")
                elif row["kind"] == "cue":
                    text = "Visual cue: " + payload["cue"].title()
                self.requests.insert("end", text)
            self.pending_ids = ids
        self.tabs.tab(self.connect_page, text=f"Connection ({len(ids)})" if ids else "Connection")

    def poll(self):
        try:
            self.refresh_requests()
            self.sync_look()
        except (AuraError, sqlite3.Error) as exc:
            self.status.set("Data unavailable: " + str(exc))
        self.poll_job = self.root.after(1000, self.poll)

    def show_studio(self):
        self.root.deiconify()
        self.root.lift()

    def hide_studio(self):
        if self.tray:
            if not self.tray.visible and (not self.floating or not self.floating.winfo_exists()):
                self.toggle_float()
            self.root.withdraw()
        else:
            self.close()

    def set_tray_visible(self):
        if not self.tray:
            raise AuraError("Tray integration is not running in this Studio-only session.")
        visible = not self.tray.visible
        if not visible and (not self.floating or not self.floating.winfo_exists()):
            self.toggle_float()
        self.ui_preferences.save(visible)
        self.tray.visible = visible
        self.status.set("Tray icon shown." if visible else "Tray icon hidden. Restore through Aura's wheel Menu, or relaunch ProjectAura.exe to reopen Studio.")

    def open_menu(self):
        menu = tk.Menu(self.root, tearoff=False, bg=PANEL, fg=TEXT)
        menu.add_command(label="Open Studio", command=self.show_studio)
        menu.add_command(label="Hide Studio", command=self.hide_studio)
        menu.add_command(label="Show tray icon" if self.tray and not self.tray.visible else "Hide tray icon",
                         command=lambda: self.safe(self.set_tray_visible), state="normal" if self.tray else "disabled")
        menu.add_command(label="Models & animations", command=lambda: (self.show_studio(), self.tabs.select(self.model_page)))
        menu.add_command(label="Dock left", command=lambda: self.dock_avatar("left"))
        menu.add_command(label="Dock right", command=lambda: self.dock_avatar("right"))
        menu.add_separator()
        menu.add_command(label="Quit Aura", command=self.close)
        self.active_menu = menu
        x,y=self.root.winfo_pointerxy()
        menu.tk_popup(x,y)

    def lifecycle_poll(self):
        if self.instance and self.instance.requested():
            self.show_studio()
        if self.tray:
            import queue
            while True:
                try:command=self.tray.commands.get_nowait()
                except queue.Empty:break
                action={"studio":self.show_studio,"float":self.toggle_float,"pause":self.pause,"tray":self.set_tray_visible,"quit":self.close}[command]
                self.safe(action)
                if command=="quit":return
        self.lifecycle_job=self.root.after(100,self.lifecycle_poll)

    def close(self):
        self.app_meter = None
        self.speech.stop()
        if self.lifecycle_job:
            self.root.after_cancel(self.lifecycle_job)
            self.lifecycle_job = None
        if self.tray:
            self.tray.close()
            self.tray = None
        if self.instance:
            self.instance.close()
            self.instance = None
        if self.showcase:
            self.showcase.close()
        if self.demo_job:
            self.root.after_cancel(self.demo_job)
        if self.voice_job:
            self.root.after_cancel(self.voice_job)
        if self.poll_job:
            self.root.after_cancel(self.poll_job)
        self.root.destroy()


def run(path=None, studio=False):
    prepare_display()
    store=Store(path)
    from .tray import Instance, Tray
    instance=Instance(store.path)
    if not instance.primary:
        instance.close()
        return
    root = tk.Tk()
    if not studio:root.withdraw()
    try:
        app=App(root, store)
        app.instance=instance
        if not studio and os.name=="nt":
            try:
                app.tray=Tray(app.ui_preferences.tray_visible)
                app.toggle_float()
            except Exception as exc:
                if app.tray:app.tray.close()
                app.tray=None
                app.show_studio()
                app.status.set("Tray unavailable; Studio stays open: " + str(exc))
        else:
            app.show_studio()
        app.lifecycle_poll()
    except (AuraError, sqlite3.Error, OSError) as exc:
        root.withdraw()
        messagebox.showerror("Aura could not start", str(exc), parent=root)
        instance.close()
        root.destroy()
        return
    root.mainloop()


def prepare_display():
    if os.name == "nt":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass

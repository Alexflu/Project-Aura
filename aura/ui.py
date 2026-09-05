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

PANEL, TEXT, MUTED, ACCENT = "#19212F", "#F0F1F8", "#A5B2C8", "#B6A0FF"


class App:
    def __init__(self, root, store):
        self.root, self.store = root, store
        root.tk.call("tk", "scaling", 4 / 3)
        self.preview = None
        self.floating = None
        self.pending_ids = []
        self.poll_job = None
        self.root.title("Project Aura · Appearance Lab")
        self.root.geometry("1120x800+30+30")
        self.root.minsize(1080, 780)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.report_callback_exception = lambda typ, exc, tb: messagebox.showerror("Aura", str(exc), parent=root)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(16, 12), font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", "#2A3047")], foreground=[("selected", TEXT)])
        style.configure("TCombobox", fieldbackground="#273145", background="#273145", foreground=TEXT, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", "#273145")], foreground=[("readonly", TEXT)])
        self.label(root, "PROJECT AURA", size=12, color=ACCENT).pack(anchor="w", padx=30, pady=(22, 0))
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=30, pady=(5, 16))
        self.label(header, "A presence that grows with you.", size=23, bold=True).pack(side="left")
        self.pause_btn = self.button(header, "Pause Aura", self.pause)
        self.pause_btn.pack(side="right")
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=24)
        left = tk.Frame(body, bg=BG, width=345)
        left.pack(side="left", fill="y", padx=(0, 24))
        left.pack_propagate(False)
        self.avatar = Avatar(left, store.read()["look"], width=340, height=440)
        self.avatar.pack(fill="both", expand=True)
        self.mode_label = self.label(left, "CURRENT APPEARANCE", size=10, color=ACCENT)
        self.mode_label.pack(pady=(0, 8))
        self.label(left, "Aura / reference avatar", size=18, bold=True).pack()
        self.label(left, "Original 2D model · bounded customization", size=10, color=MUTED).pack(pady=(6, 14))
        self.button(left, "Float on desktop", self.toggle_float).pack(fill="x", pady=(0, 8))
        self.label(left, "Offline appearance tools are ready.\nChatGPT connects separately through MCP.", size=10, color=MUTED).pack(pady=(2, 12))
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(side="left", fill="both", expand=True)
        self.look_page = self.page("Appearance")
        self.prefs_page = self.page("Your interests")
        self.connect_page = self.page("Connection")
        self.data_page = self.page("Your data")
        self.build_appearance()
        self.build_preferences()
        self.build_connection()
        self.build_data()
        self.status = tk.StringVar(value="Ready. Start with a look, or share a few interests.")
        tk.Label(root, textvariable=self.status, bg="#171D2A", fg=TEXT, anchor="w", padx=22,
                 pady=12, wraplength=1020, font=("Segoe UI", 10)).pack(fill="x", pady=(18, 0))
        self.load_preferences()
        self.sync_look()
        self.poll()

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
        return ttk.Combobox(parent, textvariable=variable, values=choices, state="readonly", width=20)

    def check(self, parent, text, variable):
        w = tk.Checkbutton(parent, text=text, variable=variable, bg=PANEL, fg=TEXT,
                           selectcolor="#293348", activebackground=PANEL, activeforeground=TEXT,
                           font=("Segoe UI", 10), anchor="w", wraplength=470, justify="left")
        w.pack(anchor="w", pady=3)
        return w

    def build_appearance(self):
        p = self.look_page
        self.label(p, "Make her feel like Aura.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Preview a new look before applying it. Her face stays consistent while hair, clothes, colors and proportions change.")
        grid = tk.Frame(p, bg=PANEL)
        grid.pack(fill="x", pady=(0, 14))
        self.look_vars = {}
        for i, (field, choices) in enumerate(OPTIONS.items()):
            self.label(grid, field.title()).grid(row=i, column=0, sticky="w", padx=(0, 24), pady=5)
            var = tk.StringVar(value=self.store.read()["look"][field])
            self.look_vars[field] = var
            box = self.combo(grid, var, choices)
            box.grid(row=i, column=1, sticky="ew", pady=5)
            box.bind("<<ComboboxSelected>>", lambda e: self.preview_controls())
        grid.columnconfigure(1, weight=1)
        self.label(p, "Or describe a look", size=11, bold=True).pack(anchor="w")
        self.request = tk.Entry(p, bg="#273145", fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 11))
        self.request.pack(fill="x", ipady=9, pady=(8, 6))
        self.request.insert(0, "ocean bob with headphones")
        self.request.bind("<Return>", lambda e: self.safe(self.preview_request))
        self.paragraph(p, "Offline keyword matching. Try palette names, hairstyles, outfits or your saved interests. This field is not a general chat.")
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill="x")
        self.button(row, "Preview request", self.preview_request).pack(side="left", padx=(0, 8))
        self.button(row, "Apply look", self.apply_preview, True).pack(side="left")
        row2 = tk.Frame(p, bg=PANEL)
        row2.pack(fill="x", pady=(10, 0))
        self.button(row2, "Discard preview", self.discard).pack(side="left", padx=(0, 8))
        self.button(row2, "Undo last change", self.undo).pack(side="left")

    def set_preview(self, look, reason):
        self.preview = validate_look(look)
        self.avatar.look = look.copy()
        for k, v in look.items():
            self.look_vars[k].set(v)
        self.mode_label.configure(text="PREVIEW · NOT YET APPLIED")
        self.status.set(reason)

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
        self.paragraph(p, "An optional MCP connection lets ChatGPT propose looks and ask to open Notepad. You approve each request here. Enabling this switch alone does not connect your account.")
        self.bridge_var, self.share_var = tk.BooleanVar(), tk.BooleanVar()
        self.check(p, "Allow requests from my connected MCP client", self.bridge_var)
        self.check(p, "Also share my interests and favorite palette", self.share_var)
        self.button(p, "Save connection settings", self.save_preferences, True).pack(anchor="w", pady=8)
        self.paragraph(p, "Connection setup is in docs/chatgpt.md. Local desktop clients can use stdio; ChatGPT may require Secure MCP Tunnel and developer access. No ChatGPT cookies, passwords or API keys are used by this beta.")
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

    def selected_request(self):
        selection = self.requests.curselection()
        if not selection:
            raise AuraError("Select a pending request first.")
        return self.pending_ids[selection[0]]

    def review(self):
        request_id = self.selected_request()
        row = next((r for r in self.store.pending() if r["id"] == request_id), None)
        if row is None:
            raise AuraError("Request expired or was already reviewed.")
        payload = json.loads(row["payload"])
        detail = "Open Windows Notepad?" if row["kind"] == "launch" else "Apply these avatar changes?\n\n" + "\n".join(f"{k.title()}: {v}" for k,v in payload.items())
        if row["kind"] == "appearance":
            self.set_preview(dict(self.store.read()["look"], **payload), "Reviewing an MCP appearance proposal.")
            self.root.update_idletasks()
        if messagebox.askyesno("Review request from connected client", detail, parent=self.root):
            self.status.set(self.store.resolve(request_id, True, launch))
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

    def build_data(self):
        p = self.data_page
        self.label(p, "Your preferences, your control.", size=17, bold=True).pack(anchor="w")
        self.paragraph(p, "Aura stores appearance, up to 20 previous looks, selected interests, activity counts, settings and up to 100 request records on this computer. There is no telemetry, microphone recording or screen capture.")
        self.paragraph(p, "Data is not encrypted. Other programs running as you may read it. Sharing through MCP is off by default; when enabled, tool inputs and results may be processed by your connected provider.")
        self.button(p, "Export my preferences", self.export).pack(anchor="w", pady=(0, 10))
        self.button(p, "Forget my data and reset Aura", self.forget).pack(anchor="w", pady=(0, 16))
        self.paragraph(p, "Reset clears Aura's local preferences, history and request records, and disables the connection. It does not erase exports, disk backups or information already shared with another service.")
        self.label(p, "Beta " + __version__, color=ACCENT, bold=True).pack(anchor="w", pady=(12, 0))
        self.paragraph(p, "This beta changes a procedural 2D avatar. It does not edit AI model weights, generate 3D meshes, control games, or design machine parts. Project Aura is independent of OpenAI.")
        path = self.paragraph(p, "Local data: " + str(self.store.path))
        path.configure(wraplength=490)

    def export(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="Export Aura data", defaultextension=".json", initialfile="aura-preferences.json", filetypes=[("JSON", "*.json")])
        if path:
            if Path(path).resolve() == self.store.path.resolve():
                raise AuraError("Choose an export filename different from Aura's database.")
            Path(path).write_text(json.dumps({"schema": 1, "preferences": self.store.read()}, indent=2), encoding="utf-8")
            self.status.set("Preferences exported. Keep the file private if it contains personal interests.")

    def forget(self):
        if messagebox.askyesno("Reset Aura", "Clear local preferences, appearance history and queued requests? This cannot be undone.", parent=self.root):
            self.store.forget()
            self.preview = None
            self.load_preferences()
            self.sync_look()
            self.refresh_requests()
            self.status.set("Local data reset. Connection disabled.")

    def pause(self):
        self.store.set_paused(not self.store.read()["paused"])
        self.preview = None
        self.sync_look()
        self.refresh_requests()
        self.status.set("Paused; pending requests cancelled." if self.store.read()["paused"] else "Aura resumed.")

    def sync_look(self):
        state = self.store.read()
        if self.preview is None:
            self.avatar.look = state["look"].copy()
            for key, var in self.look_vars.items():
                var.set(state["look"][key])
            self.mode_label.configure(text="PAUSED" if state["paused"] else "CURRENT APPEARANCE")
        self.avatar.reduced = state["reduced_motion"]
        self.avatar.paused = state["paused"]
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
            return
        window = tk.Toplevel(self.root)
        self.floating = window
        window.title("Aura · drag to move")
        window.geometry("250x340+60+90")
        window.attributes("-topmost", True)
        window.configure(bg=BG)
        if os.name == "nt":
            window.attributes("-transparentcolor", BG)
        self.float_avatar = Avatar(window, self.store.read()["look"], width=245, height=285)
        self.float_avatar.pack(fill="both", expand=True)
        self.float_avatar.bind("<ButtonPress-1>", lambda e: setattr(self, "drag", (e.x_root-window.winfo_x(), e.y_root-window.winfo_y())))
        self.float_avatar.bind("<B1-Motion>", lambda e: window.geometry(f"+{max(0,e.x_root-self.drag[0])}+{max(0,e.y_root-self.drag[1])}"))
        self.button(window, "Hide avatar", self.toggle_float).pack(fill="x")
        self.sync_look()

    def refresh_requests(self):
        pending = self.store.pending()
        ids = [r["id"] for r in pending]
        if ids != self.pending_ids:
            self.requests.delete(0, "end")
            for row in pending:
                payload = json.loads(row["payload"])
                text = "Open Notepad" if row["kind"] == "launch" else "Appearance: " + ", ".join(payload.values())
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

    def close(self):
        if self.poll_job:
            self.root.after_cancel(self.poll_job)
        self.root.destroy()


def run(path=None):
    prepare_display()
    root = tk.Tk()
    try:
        App(root, Store(path))
    except (AuraError, sqlite3.Error, OSError) as exc:
        root.withdraw()
        messagebox.showerror("Aura could not start", str(exc), parent=root)
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

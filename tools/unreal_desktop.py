"""Visible controls for the local 3D desktop-presence prototype."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura.embodied_speech import EmbodiedSpeech
from aura.embodiment import write_snapshot
from tools.unreal_body import PROJECT, installed_engine, launch_command, runtime_environment


class DesktopControls:
    def __init__(self, root, engine, smoke_seconds=0):
        self.root = root
        self.bridge = EmbodiedSpeech()
        self.process = None
        self.ready = False
        self.ready_since = 0
        self.closed = False
        self.started = time.monotonic()
        self.smoke_seconds = smoke_seconds
        self.last_error = ""
        self.folder = PROJECT.parent / "Saved/Aura/Desktop" / uuid.uuid4().hex[:10]
        self.folder.mkdir(parents=True)
        root.title("Aura — Desktop controls")
        root.geometry("480x210")
        root.resizable(False, False)
        panel = ttk.Frame(root, padding=16)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Aura desktop prototype", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Local speech • Drag Aura to move her • Right-click Aura to close").pack(anchor="w", pady=(4, 10))
        self.entry = ttk.Entry(panel)
        self.entry.insert(0, "Hello Alex. I'm here on your desktop.")
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", lambda event: self.speak())
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=10)
        self.speak_button = ttk.Button(row, text="Speak", command=self.speak, state="disabled")
        self.speak_button.pack(side="left")
        ttk.Button(row, text="Stop", command=self.stop).pack(side="left", padx=5)
        self.pause_button = ttk.Button(row, text="Pause", command=self.pause)
        self.pause_button.pack(side="left")
        ttk.Button(row, text="Close Aura", command=self.close).pack(side="right")
        self.status = tk.StringVar(value="Loading the 3D character…")
        ttk.Label(panel, textvariable=self.status, wraplength=445).pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)
        command = [arg.replace("t.MaxFPS 60", "t.MaxFPS 30") for arg in launch_command(engine, metahuman=True)]
        self.process = subprocess.Popen(command + ["-AuraDesktop", "-AuraSpeechAudio", f"-AuraDataDir={self.folder}"], env=runtime_environment())
        root.after(50, self.tick)

    def speak(self):
        if not self.ready or self.bridge.behavior.paused:
            return
        try:
            self.bridge.speak(self.entry.get())
            self.last_error = ""
        except Exception as exc:
            self.last_error = str(exc)
            self.status.set(self.last_error)

    def stop(self):
        self.bridge.stop()
        self.last_error = ""

    def pause(self):
        if self.bridge.behavior.paused:
            self.bridge.behavior.paused = False
            self.pause_button.configure(text="Pause")
            self.speak_button.configure(state="normal" if self.ready else "disabled")
        else:
            self.bridge.pause()
            self.pause_button.configure(text="Resume")
            self.speak_button.configure(state="disabled")

    def tick(self):
        if self.closed:
            return
        try:
            if self.process.poll() is not None:
                self.close()
                return
            write_snapshot(self.folder / "behavior.json", self.bridge.snapshot(1 / 30))
            if not self.ready:
                if (self.folder / "desktop-ready.json").exists():
                    self.ready = True
                    self.ready_since = time.time()
                    self.speak_button.configure(state="disabled" if self.bridge.behavior.paused else "normal")
                    self.status.set("Ready. Local voice only; no live AI connection.")
                    if self.smoke_seconds:
                        self.root.after(int(self.smoke_seconds * 1000), self.close)
                elif time.monotonic() - self.started > 180:
                    raise RuntimeError("Desktop setup timed out. Check the Unreal build and local MetaHuman assembly.")
            elif time.time() - ((self.folder / "desktop-status.json").stat().st_mtime
                                if (self.folder / "desktop-status.json").exists() else self.ready_since) > 4:
                raise RuntimeError("The 3D renderer stopped responding. Close Aura and try again.")
            else:
                self.status.set(self.last_error or ("Paused" if self.bridge.behavior.paused else
                                ("Speaking…" if self.bridge.speech.state == "playing" else "Ready. Local voice only; no live AI connection."))
                                )
            self.root.after(33, self.tick)
        except Exception as exc:
            self.ready = False
            self.bridge.stop()
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=15)
            self.speak_button.configure(state="disabled")
            self.status.set(str(exc))

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.bridge.stop()
            write_snapshot(self.folder / "behavior.json", self.bridge.snapshot(0))
        finally:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=15)
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--smoke-seconds", type=float, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = tk.Tk()
    try:
        controls = DesktopControls(root, args.engine_root or installed_engine(), args.smoke_seconds)
        root.mainloop()
    finally:
        if "controls" in locals():
            controls.close()
        else:
            root.destroy()


if __name__ == "__main__":
    main()

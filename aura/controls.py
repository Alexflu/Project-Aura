"""Display labels separate from stable saved/MCP values."""
import tkinter as tk
from tkinter import ttk

LABELS = {
    "violet": "Amethyst", "ocean": "Cyan", "forest": "Jade", "ember": "Ember",
    "rose": "Rose", "slate": "Silver", "long": "Long waves", "pixie": "Layered crop",
    "bob": "Bob / short", "tactical": "Tactical Ops", "stealth": "Stealth Striker",
    "explorer": "Explorer · classic", "engineer": "Engineer · classic", "casual": "Casual · classic",
    "solid": "Solid", "hologram": "Hologram", "default": "Windows default",
}


class Choice(ttk.Combobox):
    def __init__(self, parent, model, choices):
        self.model = model
        self.names = {value: LABELS.get(value, value.replace("_", " ").title()) for value in choices}
        self.values_by_name = {name: value for value, name in self.names.items()}
        self.display = tk.StringVar(parent, value=self.names.get(model.get(), model.get()))
        self.updating = False
        super().__init__(parent, textvariable=self.display, values=list(self.names.values()), state="readonly", width=20)
        self.model_trace = model.trace_add("write", self.from_model)
        self.display_trace = self.display.trace_add("write", self.from_display)
        self.bind("<Destroy>", self.cleanup)

    def from_model(self, *_):
        if not self.updating:
            self.updating = True
            try:
                self.display.set(self.names.get(self.model.get(), self.model.get()))
            finally:
                self.updating = False

    def from_display(self, *_):
        if not self.updating and self.display.get() in self.values_by_name:
            self.updating = True
            try:
                self.model.set(self.values_by_name[self.display.get()])
            finally:
                self.updating = False

    def cleanup(self, event):
        if event.widget is self:
            self.model.trace_remove("write", self.model_trace)
            self.display.trace_remove("write", self.display_trace)

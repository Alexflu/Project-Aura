"""Offline semantic behavior controller. No device access or cloud connection."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
import time
import uuid


def number(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Expected a finite number in [{low}, {high}]")
    return float(value)


def validate_command(value):
    """Strict v1 envelope; commands never contain paths, scripts or device actions."""
    if not isinstance(value, dict) or set(value) != {"version", "id", "action", "params"}:
        raise ValueError("Expected version, id, action and params")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Unsupported behavior version")
    if not isinstance(value["id"], str) or not 1 <= len(value["id"]) <= 64:
        raise ValueError("Command id must contain 1..64 characters")
    action, params = value["action"], value["params"]
    fields = {"idle": set(), "listen": set(), "speak": {"duration_s"},
              "look_at": {"x", "y", "z"}, "gesture": {"name", "duration_s"},
              "walk_to": {"x", "y"}, "expression": {"name", "intensity"},
              "posture": {"name"}, "blush": {"intensity"},
              "pause": set(), "resume": set()}
    if not isinstance(action, str) or action not in fields or not isinstance(params, dict) or set(params) != fields[action]:
        raise ValueError("Unsupported action or parameters")
    params = dict(params)
    for key in ("x", "y", "z"):
        if key in params:
            params[key] = number(params[key], -500, 500)
    if "duration_s" in params:
        params["duration_s"] = number(params["duration_s"], .05, 10)
    if "intensity" in params:
        params["intensity"] = number(params["intensity"], 0, 1)
    if action == "gesture" and params["name"] not in ("wave", "nod"):
        raise ValueError("Unsupported gesture")
    if action == "expression" and params["name"] not in ("neutral", "happy", "curious", "concerned"):
        raise ValueError("Unsupported expression")
    if action == "posture" and params["name"] not in ("neutral", "attentive", "relaxed"):
        raise ValueError("Unsupported posture")
    return {**value, "params": params}


class BehaviorController:
    """Single-threaded demo state, with bounded speed and expiring transient cues."""
    def __init__(self):
        self.session = str(uuid.uuid4())
        self.sequence = 0
        self.paused = False
        self.mode = "idle"
        self.position = [0.0, 0.0]
        self.target = list(self.position)
        self.gaze = [200.0, 0.0, 160.0]
        self.gesture = "none"
        self.gesture_remaining = 0.0
        self.expression = "neutral"
        self.expression_intensity = 0.0
        self.posture = "neutral"
        self.blush = 0.0
        self.speech_remaining = 0.0
        self.speech_elapsed = 0.0
        self._seen = set()

    def stop(self):
        self.mode = "idle"
        self.target = list(self.position)
        self.gesture = "none"
        self.gesture_remaining = self.speech_remaining = 0.0

    def apply(self, command):
        command = validate_command(command)
        identifier, action, p = command["id"], command["action"], command["params"]
        if identifier in self._seen:
            return "duplicate"
        if len(self._seen) >= 4096:
            raise ValueError("Demo session command limit reached; start a new session")
        self._seen.add(identifier)
        if action == "pause":
            self.stop()
            self.paused = True
        elif action == "resume":
            self.paused = False
        elif self.paused:
            return "paused"
        elif action == "idle":
            self.stop()
        elif action == "listen":
            self.stop()
            self.mode = "listening"
        elif action == "speak":
            self.mode = "speaking"
            self.speech_remaining = p["duration_s"]
            self.speech_elapsed = 0.0
        elif action == "look_at":
            self.gaze = [p[k] for k in ("x", "y", "z")]
        elif action == "gesture":
            self.gesture, self.gesture_remaining = p["name"], p["duration_s"]
        elif action == "walk_to":
            self.target = [p["x"], p["y"]]
        elif action == "expression":
            self.expression = p["name"]
            self.expression_intensity = p["intensity"]
        elif action == "posture":
            self.posture = p["name"]
        elif action == "blush":
            self.blush = p["intensity"]
        return "accepted"

    def tick(self, dt):
        dt = number(dt, 0, .25)
        if self.paused:
            return
        dx, dy = (self.target[i] - self.position[i] for i in range(2))
        distance = math.hypot(dx, dy)
        if distance:
            ratio = min(1, 100 * dt / distance)  # centimeters per second
            self.position = [self.position[0] + dx * ratio, self.position[1] + dy * ratio]
        self.gesture_remaining = max(0, self.gesture_remaining - dt)
        if not self.gesture_remaining:
            self.gesture = "none"
        self.speech_elapsed += dt
        self.speech_remaining = max(0, self.speech_remaining - dt)
        if self.mode == "speaking" and not self.speech_remaining:
            self.mode = "idle"

    def snapshot(self):
        self.sequence += 1
        return {"version": 1, "session": self.session, "sequence": self.sequence,
                "paused": self.paused, "mode": self.mode,
                "x": self.position[0], "y": self.position[1],
                "moving": not self.paused and math.dist(self.position, self.target) > .01,
                "gaze_x": self.gaze[0], "gaze_y": self.gaze[1], "gaze_z": self.gaze[2],
                "gesture": self.gesture,
                "expression": self.expression, "expression_intensity": self.expression_intensity,
                "posture": self.posture, "blush": self.blush,
                "mouth_open": (0.25 + .65 * abs(math.sin(self.speech_elapsed * 12)))
                if self.mode == "speaking" and not self.paused else 0.0}


def write_snapshot(path, snapshot):
    """Atomic replacement keeps a concurrent reader from observing partial JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".aura-", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            json.dump(snapshot, stream, allow_nan=False, separators=(",", ":"))
        # Windows readers may briefly deny replacement while their handle is open.
        # Keep the old complete snapshot and retry briefly, never write in place.
        for attempt in range(6):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(.01)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)

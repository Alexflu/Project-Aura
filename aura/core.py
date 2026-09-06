"""AuraCore: validated appearance, explicit preferences and transactional state."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

OPTIONS = {
    "palette": ("violet", "ocean", "forest", "ember", "rose", "slate"),
    "hair": ("long", "bob", "pixie"),
    "outfit": ("explorer", "engineer", "casual", "tactical", "stealth"),
    "accessory": ("none", "headphones", "goggles", "leaf"),
    "silhouette": ("balanced", "compact", "tall"),
}
DEFAULT_LOOK = dict(zip(OPTIONS, ("violet", "pixie", "tactical", "none", "balanced")))
INTERESTS = ("making", "gaming", "music", "nature", "fitness", "art")
INTEREST_LOOKS = {
    "making": {"outfit": "engineer", "accessory": "goggles", "palette": "ember"},
    "gaming": {"outfit": "tactical", "accessory": "headphones", "palette": "violet"},
    "music": {"outfit": "casual", "accessory": "headphones", "palette": "ocean"},
    "nature": {"outfit": "explorer", "accessory": "leaf", "palette": "forest"},
    "fitness": {"outfit": "casual", "accessory": "none", "palette": "ember"},
    "art": {"outfit": "explorer", "accessory": "none", "palette": "rose"},
}


class AuraError(ValueError):
    pass


def validate_cue(value):
    if not isinstance(value, dict) or set(value) != {"cue"} or value["cue"] not in ("entrance", "cast", "reveal", "stow", "wave", "inspect", "draw"):
        raise AuraError("Choose entrance, cast, reveal, stow, wave, inspect or draw. Visual cues cannot execute commands.")
    return dict(value)


def validate_performance(value):
    if (not isinstance(value, dict) or set(value) != {"text", "mood"} or
            not isinstance(value["text"], str) or len(value["text"]) > 1000 or
            value["mood"] not in ("neutral", "happy", "thoughtful", "focused", "sleepy")):
        raise AuraError("Use a supported mood and up to 1,000 characters of speech text.")
    return dict(value)


def validate_look(value, partial=False):
    if not isinstance(value, dict) or not value or set(value) - OPTIONS.keys():
        raise AuraError("Use only the supported appearance fields.")
    if not partial and set(value) != OPTIONS.keys():
        raise AuraError("The appearance is incomplete.")
    for key, item in value.items():
        if not isinstance(item, str) or item not in OPTIONS[key]:
            raise AuraError(f"Unsupported {key}. Choose: {', '.join(OPTIONS[key])}.")
    return dict(value)


def parse_request(text):
    """Offline keyword matching, intentionally not advertised as AI inference."""
    if not isinstance(text, str) or len(text) > 1000:
        raise AuraError("Keep the request under 1,000 characters.")
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & {"not", "no", "without", "except", "dont", "don"}:
        raise AuraError("For exclusions, use the appearance controls so the change is precise.")
    patch = {}
    for interest in INTERESTS:
        if interest in words:
            patch.update(INTEREST_LOOKS[interest])
    for field, choices in OPTIONS.items():
        matches = [item for item in choices if item in words]
        if len(matches) > 1:
            raise AuraError(f"Choose one {field} at a time.")
        if matches:
            patch[field] = matches[0]
    if not patch:
        raise AuraError("Try 'ocean bob with headphones' or use the appearance controls.")
    return patch


def data_path():
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return base / "ProjectAura" / "aura.sqlite3"


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise AuraError("This data belongs to a newer Aura version. It was not changed.")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, look TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, kind TEXT NOT NULL,
                    payload TEXT NOT NULL, created REAL NOT NULL, status TEXT NOT NULL, result TEXT NOT NULL);
                PRAGMA user_version=1;
            """)
            db.execute("INSERT OR IGNORE INTO state VALUES(1, ?)", (json.dumps(self.defaults()),))
        self.read()

    @staticmethod
    def defaults():
        return {"look": DEFAULT_LOOK.copy(), "interests": [], "habits": {}, "favorite": "violet",
                "adapt": False, "bridge": False, "share": False, "paused": False, "reduced_motion": False}

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _state(self, db):
        try:
            state = json.loads(db.execute("SELECT value FROM state WHERE id=1").fetchone()[0])
            validate_look(state["look"])
            if set(state) != set(self.defaults()):
                raise ValueError()
            if not isinstance(state["interests"], list) or any(x not in INTERESTS for x in state["interests"]):
                raise ValueError()
            if not isinstance(state["habits"], dict) or any(k not in INTERESTS or type(v) is not int or not 0 <= v <= 100 for k, v in state["habits"].items()):
                raise ValueError()
            if state["favorite"] not in OPTIONS["palette"]:
                raise ValueError()
            if any(type(state[k]) is not bool for k in ("adapt", "bridge", "share", "paused", "reduced_motion")):
                raise ValueError()
            return state
        except (KeyError, TypeError, ValueError) as exc:
            raise AuraError("Saved data could not be validated. Aura has preserved the file; restore an export or use a new data folder.") from exc

    def read(self):
        with self.connection() as db:
            return self._state(db)

    def _write(self, db, state):
        db.execute("UPDATE state SET value=? WHERE id=1", (json.dumps(state),))

    def preferences(self, interests, favorite, adapt, bridge, share, reduced_motion):
        if not isinstance(interests, list) or any(x not in INTERESTS for x in interests):
            raise AuraError("Choose supported interests.")
        if favorite not in OPTIONS["palette"] or any(type(x) is not bool for x in (adapt, bridge, share, reduced_motion)):
            raise AuraError("Invalid preference.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            state.update(interests=list(dict.fromkeys(interests)), favorite=favorite, adapt=adapt,
                         bridge=bridge, share=share, reduced_motion=reduced_motion)
            self._write(db, state)
            if not bridge:
                db.execute("UPDATE requests SET status='cancelled', result='Connection disabled' WHERE status='pending'")

    def set_paused(self, paused):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            state["paused"] = bool(paused)
            self._write(db, state)
            if paused:
                db.execute("UPDATE requests SET status='cancelled', result='Paused by user' WHERE status='pending'")

    def _apply(self, db, state, look):
        if state["paused"]:
            raise AuraError("Aura is paused. Resume before changing her appearance.")
        if look != state["look"]:
            db.execute("INSERT INTO history(look) VALUES(?)", (json.dumps(state["look"]),))
            db.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT 20)")
            state["look"] = look
            self._write(db, state)

    def apply(self, look):
        validate_look(look)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._apply(db, self._state(db), look)

    def undo(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            if state["paused"]:
                raise AuraError("Resume Aura before undoing a change.")
            row = db.execute("SELECT * FROM history ORDER BY id DESC LIMIT 1").fetchone()
            if row is None:
                raise AuraError("There is no earlier appearance to restore.")
            state["look"] = validate_look(json.loads(row["look"]))
            self._write(db, state)
            db.execute("DELETE FROM history WHERE id=?", (row["id"],))

    def suggestion(self, state=None):
        state = state or self.read()
        choices = state["interests"]
        if not choices:
            raise AuraError("Save at least one interest first.")
        interest = max(choices, key=lambda x: state["habits"].get(x, 0))
        look = dict(state["look"], **INTEREST_LOOKS[interest])
        look["palette"] = state["favorite"]
        return look, f"Inspired by {interest} and your favorite {state['favorite']} palette."

    def record_activity(self, activity):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            if state["paused"]:
                raise AuraError("Aura is paused.")
            if activity not in state["interests"]:
                raise AuraError("Save this interest before recording an activity.")
            state["habits"][activity] = min(100, state["habits"].get(activity, 0) + 1)
            self._write(db, state)
            if state["adapt"]:
                look, reason = self.suggestion(state)
                self._apply(db, state, look)
                return reason + " Applied with your automatic adaptation setting; Undo is available."
            return "Activity recorded locally. Use Suggest from interests to preview a look."

    def forget(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("PRAGMA secure_delete=ON")
            self._write(db, self.defaults())
            db.execute("DELETE FROM history")
            db.execute("DELETE FROM requests")

    def enqueue(self, kind, payload):
        if kind == "appearance":
            payload = validate_look(payload, partial=True)
        elif kind == "performance":
            payload = validate_performance(payload)
        elif kind == "cue":
            payload = validate_cue(payload)
        elif kind != "launch" or payload != {"app": "notepad"}:
            raise AuraError("Unsupported action. Use appearance, speech/mood proposals, or Notepad.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._state(db)
            if not state["bridge"] or state["paused"]:
                raise AuraError("Enable the ChatGPT connection in Aura and resume it first.")
            self._expire(db)
            if db.execute("SELECT count(*) FROM requests WHERE status='pending'").fetchone()[0] >= 10:
                raise AuraError("Review pending requests in Aura before sending more.")
            request_id = str(uuid.uuid4())
            db.execute("INSERT INTO requests VALUES(?,?,?,?,?,?)",
                       (request_id, kind, json.dumps(payload), time.time(), "pending", "Awaiting local review"))
            db.execute("DELETE FROM requests WHERE id NOT IN (SELECT id FROM requests ORDER BY created DESC LIMIT 100)")
            return {"request_id": request_id, "status": "pending", "message": "The user must review this request in Aura. Nothing has been applied or launched."}

    def _expire(self, db):
        db.execute("UPDATE requests SET status='expired', result='Request expired' WHERE status='pending' AND created<?", (time.time() - 600,))

    def pending(self):
        with self.connection() as db:
            self._expire(db)
            return [dict(r) for r in db.execute("SELECT * FROM requests WHERE status='pending' ORDER BY created")]

    def request_status(self, request_id):
        if not isinstance(request_id, str) or len(request_id) > 40:
            raise AuraError("Invalid request identifier.")
        with self.connection() as db:
            self._expire(db)
            row = db.execute("SELECT id,status,result FROM requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                raise AuraError("Request not found.")
            return dict(row)

    def resolve(self, request_id, accept, launcher, performer=None):
        """Local UI only. Never registered as an MCP tool. Claims each request once."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire(db)
            state = self._state(db)
            row = db.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
            if row is None or row["status"] != "pending":
                raise AuraError("This request is no longer pending.")
            if accept and (state["paused"] or not state["bridge"]):
                raise AuraError("The connection is disabled or Aura is paused.")
            status, result = "rejected", "Declined by user"
            if accept:
                payload = json.loads(row["payload"])
                if row["kind"] == "appearance":
                    look = dict(state["look"], **validate_look(payload, partial=True))
                    self._apply(db, state, look)
                    status, result = "applied", "Appearance applied"
                elif row["kind"] == "launch" and payload == {"app": "notepad"}:
                    status, result = "launching", "Launch approved; final outcome may be unknown if Aura exits"
                elif row["kind"] in ("performance", "cue") and performer is not None:
                    payload = validate_cue(payload) if row["kind"] == "cue" else validate_performance(payload)
                    status, result = "performing", "Performance approved; outcome unknown if Aura exits"
                else:
                    raise AuraError("Invalid stored action.")
            db.execute("UPDATE requests SET status=?,result=? WHERE id=?", (status, result, request_id))
        if status == "launching":
            try:
                result = launcher("notepad")
                status = "submitted"
            except Exception:
                status, result = "failed", "Windows could not launch Notepad. No automatic retry."
            with self.connection() as db:
                db.execute("UPDATE requests SET status=?,result=? WHERE id=?", (status, result, request_id))
        elif status == "performing":
            try:
                result = performer(payload)
                status = "submitted"
            except Exception:
                status, result = "failed", "Performance could not start. No automatic retry."
            with self.connection() as db:
                db.execute("UPDATE requests SET status=?,result=? WHERE id=?", (status, result, request_id))
        return result

    def public_state(self):
        state = self.read()
        if not state["bridge"]:
            raise AuraError("Enable the ChatGPT connection in Aura first.")
        result = {"version": "0.7.0-beta.3", "paused": state["paused"], "appearance": state["look"], "choices": OPTIONS}
        if state["share"]:
            result["preferences"] = {"interests": state["interests"], "favorite_palette": state["favorite"]}
        return result

"""Check real-time file delivery with an independent reader (not an Unreal test)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "behavior.json"
        start = time.monotonic()
        process = subprocess.Popen([sys.executable, str(root / "tools/skeleton_zero.py"),
                                    "--output", str(path)], stdout=subprocess.DEVNULL)
        observed = []
        try:
            while process.poll() is None:
                if time.monotonic() - start > 25:
                    raise RuntimeError("Replay exceeded 25 seconds")
                if path.exists():
                    # A concurrent partial write is a test failure, not silently retried.
                    try:
                        with path.open(encoding="utf-8") as stream:
                            state = json.load(stream)
                    except PermissionError:
                        # Match the receiver: retry transient Windows replacement locks.
                        time.sleep(.01)
                        continue
                    if not observed or state["sequence"] != observed[-1]["sequence"]:
                        observed.append(state)
                time.sleep(.01)
            if process.returncode:
                raise RuntimeError(f"Replay exited with {process.returncode}")
            final = json.loads(path.read_text(encoding="utf-8"))
            assert {s["mode"] for s in observed} == {"idle", "listening", "speaking"}
            assert any(s["gesture"] == "wave" for s in observed)
            assert any(s["gaze_y"] == 100 for s in observed)
            assert any(s["moving"] for s in observed)
            assert any(s["paused"] for s in observed)
            assert final["mode"] == "idle" and not final["moving"] and final["mouth_open"] == 0
            assert all(a["sequence"] < b["sequence"] for a, b in zip(observed, observed[1:]))
            assert len({s["session"] for s in observed}) == 1
            print(f"PASS: {len(observed)} distinct snapshots in {time.monotonic() - start:.2f}s; "
                  "all six cue channels, pause, final idle, no partial JSON. Unreal not tested.")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()

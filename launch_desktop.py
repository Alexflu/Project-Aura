"""Desktop entry point; packaged builds check for updates only when opened."""
import argparse
import os
import subprocess
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Aura desktop beta")
    parser.add_argument("--data", help="Alternate local SQLite file")
    parser.add_argument("--studio", action="store_true", help="Open Studio")
    parser.add_argument("--skip-update", action="store_true", help="Open without a network update check")
    parser.add_argument("--self-check", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--self-check-version", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_check:
        from aura import __version__
        if args.self_check_version and args.self_check_version != __version__:
            sys.exit(2)
        import tkinter as tk
        from aura.model_library import REFERENCE
        from aura.models import load_pack
        root = tk.Tk()
        root.withdraw()
        load_pack(REFERENCE)
        root.destroy()
        sys.exit(0)
    if getattr(sys, 'frozen', False) and os.name == 'nt' and not args.skip_update:
        from aura.core import Store
        from aura.tray import Instance
        instance = Instance(Store(args.data).path)
        if not instance.primary:
            instance.close()
            sys.exit(0)
        try:
            from aura.updater import startup
            target = startup()
        except Exception:
            target = None
        finally:
            instance.close()
        if target:
            try:
                subprocess.Popen([str(target), '--skip-update'] + sys.argv[1:])
                sys.exit(0)
            except OSError:
                pass
    from aura.ui import run
    run(args.data, studio=args.studio)

"""Launch-only GitHub updates. No scheduled task, service, or credential access."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile

from . import __version__
from .core import data_path

API = 'https://api.github.com/repos/Alexflu/Project-Aura/releases?per_page=30'
PREFIX = 'https://github.com/Alexflu/Project-Aura/releases/download/'
MAX_ZIP = 250_000_000


def version(text):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?', text)
    if not match:
        raise ValueError('Unsupported Aura version')
    return tuple(int(v) for v in match.groups()[:3]) + (int(match[4]) if match[4] else 1_000_000,)


def cache_root():
    return data_path().parent / 'updates'


def read_json(path, limit=65536):
    if path.stat().st_size > limit:
        raise ValueError('Update metadata is too large')
    return json.loads(path.read_text(encoding='utf-8'))


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            temporary = Path(f.name)
            json.dump(data, f)
        temporary.replace(path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def enabled(root=None):
    try:
        value = read_json((root or cache_root()) / 'settings.json', 1024)['enabled']
        return value if type(value) is bool else False
    except FileNotFoundError:
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def set_enabled(value):
    atomic_json(cache_root() / 'settings.json', {'enabled': bool(value)})


def cached(root=None, current=__version__, bridge=False):
    root = root or cache_root()
    try:
        data = read_json(root / 'active.json', 2048)
        selected = data['version']
        if version(selected) <= version(current):
            return None
        folder = root / selected / 'ProjectAura'
        if folder.resolve() != root.resolve() / selected / 'ProjectAura':
            return None
        path = folder / ('bridge/AuraMCP.exe' if bridge else 'ProjectAura.exe')
        expected = data['bridge_sha256' if bridge else 'desktop_sha256']
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return None
        return path
    except (OSError, ValueError, KeyError, TypeError):
        return None


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        'User-Agent': 'ProjectAura-Updater', 'Accept': 'application/vnd.github+json'}), timeout=8)


def remote_json(url, limit=2_000_000):
    with request(url) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Release metadata is too large')
    return json.loads(data)


def candidate(releases, current):
    choices = []
    for release in releases:
        try:
            tag = release['tag_name']
            number = tag.removeprefix('v')
            if release.get('draft') or version(number) <= version(current):
                continue
            name = 'ProjectAura-' + number + '-windows-x64.zip'
            assets = {a['name']: a for a in release['assets']}
            urls = [assets[n]['browser_download_url'] for n in (name, 'release-manifest.json')]
            if urls != [PREFIX + tag + '/' + n for n in (name, 'release-manifest.json')]:
                continue
            choices.append((version(number), number, name, urls))
        except (KeyError, TypeError, ValueError):
            continue
    return max(choices, default=None)


def extract(archive, destination):
    """Reject escapes, links, Windows aliases and unbounded archive expansion."""
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        if len(entries) > 15000 or sum(e.file_size for e in entries) > 1_000_000_000:
            raise ValueError('Update exceeds unpacked size limits')
        seen = set()
        for entry in entries:
            name = entry.filename
            parts = PurePosixPath(name).parts
            if (not parts or parts[0] != 'ProjectAura' or any(c in name for c in '\\:<>\"|?*') or
                any(p in ('.', '..') for p in name.split('/')) or
                any(p in ('.', '..') or p.endswith((' ', '.')) or
                    re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p) for p in parts) or
                (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('Unsafe update archive path')
            normalized = name.rstrip('/').casefold()
            if normalized in seen:
                raise ValueError('Duplicate update archive path')
            seen.add(normalized)
            if not (destination / name).resolve().is_relative_to(destination.resolve()):
                raise ValueError('Update path escapes staging')
        source.extractall(destination)
    for required in ('ProjectAura.exe', 'bridge/AuraMCP.exe'):
        if not (destination / 'ProjectAura' / required).is_file():
            raise ValueError('Incomplete Aura update')


def install(release, root, cancelled, status):
    _, number, name, urls = release
    manifest = remote_json(urls[1], 65536)
    if manifest['version'] != number:
        raise ValueError('Release version mismatch')
    expected = manifest['assets'][name]
    size, digest = expected['bytes'], expected['sha256']
    if type(size) is not int or not 0 < size <= MAX_ZIP or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Invalid update integrity metadata')
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root, prefix='staging-') as temp:
        staging = Path(temp)
        archive = staging / 'update.zip'
        checksum = hashlib.sha256()
        received = 0
        deadline = time.monotonic() + 120
        with request(urls[0]) as response, archive.open('wb') as output:
            while chunk := response.read(256 * 1024):
                if cancelled.is_set() or time.monotonic() > deadline:
                    raise ValueError('Update cancelled or timed out')
                received += len(chunk)
                if received > size:
                    raise ValueError('Update is larger than declared')
                checksum.update(chunk)
                output.write(chunk)
                status[0] = f'Downloading Aura {number}… {received * 100 // size}%'
        if received != size or checksum.hexdigest() != digest:
            raise ValueError('Update checksum mismatch')
        if cancelled.is_set():
            return
        status[0] = 'Checking the new Aura build…'
        extract(archive, staging)
        folder = staging / 'ProjectAura'
        subprocess.run([str(folder / 'ProjectAura.exe'), '--self-check', '--self-check-version', number], check=True,
                       timeout=25, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if cancelled.is_set():
            return
        target = root / number
        if target.exists():
            raise ValueError('An update folder already exists; keeping the current version')
        hashes = {'version': number,
                  'desktop_sha256': hashlib.sha256((folder / 'ProjectAura.exe').read_bytes()).hexdigest(),
                  'bridge_sha256': hashlib.sha256((folder / 'bridge/AuraMCP.exe').read_bytes()).hexdigest()}
        archive.unlink()
        staging.rename(target)
        atomic_json(root / 'active.json', hashes)


def startup():
    """A cancellable foreground check, once per launch; failures use the last good copy."""
    import tkinter as tk
    root = cache_root()
    from .tray import Instance
    guard = Instance(root / 'update-lock')
    if not guard.primary:
        guard.close()
        return cached(root)
    window = None
    cancelled = threading.Event()
    done = threading.Event()
    status = ['Checking for an Aura update…']
    def worker():
        try:
            current = __version__
            if cached(root):
                current = read_json(root / 'active.json')['version']
            release = candidate(remote_json(API), current)
            if release and not cancelled.is_set():
                install(release, root, cancelled, status)
        except Exception:
            # Offline, blocked, invalid or failed builds must never block opening Aura.
            status[0] = 'Update unavailable. Opening your installed Aura.'
        finally:
            done.set()
    try:
        if enabled(root):
            window = tk.Tk()
            window.title('Project Aura · Update')
            window.geometry('460x145')
            text = tk.StringVar(value=status[0])
            tk.Label(window, textvariable=text, padx=16, pady=20).pack()
            def cancel():
                cancelled.set()
                window.quit()
            tk.Button(window, text='Open installed version now', command=cancel).pack()
            window.protocol('WM_DELETE_WINDOW', cancel)
            threading.Thread(target=worker, daemon=True).start()
            def poll():
                text.set(status[0])
                if done.is_set():
                    window.quit()
                else:
                    window.after(100, poll)
            window.after(100, poll)
            window.mainloop()
    finally:
        if window:
            window.destroy()
        # Cancellation retains the lock until the bounded worker has stopped.
        if cancelled.is_set() and not done.is_set():
            def release_guard():
                done.wait()
                guard.close()
            threading.Thread(target=release_guard, daemon=True).start()
        else:
            guard.close()
    return cached(root)

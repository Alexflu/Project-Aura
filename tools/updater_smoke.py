"""Verify staging and preflight using a real built ZIP and a disposable update cache."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aura import __version__
from aura import updater as u

archive = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path('artifacts') / f'ProjectAura-{__version__}-windows-x64.zip').resolve()
name = 'ProjectAura-' + __version__ + '-windows-x64.zip'
manifest = {'version': __version__, 'assets': {name: {
    'bytes': archive.stat().st_size, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}}}
with tempfile.TemporaryDirectory(prefix='aura-update-test-') as temp:
    root = Path(temp)
    with patch.object(u, 'remote_json', return_value=manifest), \
         patch.object(u, 'request', side_effect=lambda url: archive.open('rb')):
        u.install((u.version(__version__), __version__, name, ['local-zip', 'local-manifest']),
                  root, threading.Event(), [''])
    desktop = u.cached(root, current='0.0.0')
    bridge = u.cached(root, current='0.0.0', bridge=True)
    assert desktop and bridge
    assert json.loads((root / 'active.json').read_text())['version'] == __version__
    assert not list(root.glob('staging-*'))
print('Real updater installation passed: ZIP integrity, extraction, packaged version/startup preflight, desktop and bridge selection.')

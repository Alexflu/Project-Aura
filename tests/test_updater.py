import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from aura import updater as u


def archive_bytes(extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('ProjectAura/ProjectAura.exe', b'desktop')
        z.writestr('ProjectAura/bridge/AuraMCP.exe', b'bridge')
        if extra:
            z.writestr(*extra)
    return stream.getvalue()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.number = '0.8.0-beta.1'
        self.name = 'ProjectAura-' + self.number + '-windows-x64.zip'
        self.release = (u.version(self.number), self.number, self.name, ['archive', 'manifest'])
        self.data = archive_bytes()
        self.manifest = {'version': self.number, 'assets': {self.name: {
            'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest()}}}

    def install(self, **kwargs):
        with patch.object(u, 'remote_json', return_value=self.manifest), \
             patch.object(u, 'request', return_value=io.BytesIO(self.data)), \
             patch.object(u.subprocess, 'run', **kwargs):
            u.install(self.release, self.root, threading.Event(), [''])

    def test_beta_and_stable_ordering(self):
        self.assertGreater(u.version('0.8.0'), u.version('0.8.0-beta.99'))
        self.assertGreater(u.version('0.8.0-beta.10'), u.version('0.8.0-beta.2'))
        for bad in ('../test', 'latest', 'v1.2.3', '1.2'):
            with self.assertRaises(ValueError): u.version(bad)

    def test_only_newer_official_assets_are_selected(self):
        tag = 'v' + self.number
        release = {'tag_name': tag, 'draft': False, 'assets': [
            {'name': name, 'browser_download_url': u.PREFIX + tag + '/' + name}
            for name in (self.name, 'release-manifest.json')]}
        self.assertIsNotNone(u.candidate([release], '0.7.0-beta.4'))
        self.assertIsNone(u.candidate([release], self.number))
        release['assets'][0]['browser_download_url'] = 'https://example.com/evil.exe'
        self.assertIsNone(u.candidate([release], '0.7.0-beta.4'))

    def test_verified_install_and_cached_bridge(self):
        self.install(return_value=None)
        self.assertEqual(u.cached(self.root, '0.7.0-beta.4').read_bytes(), b'desktop')
        self.assertEqual(u.cached(self.root, '0.7.0-beta.4', bridge=True).read_bytes(), b'bridge')
        self.assertIsNone(u.cached(self.root, self.number))
        (self.root / self.number / 'ProjectAura/ProjectAura.exe').write_bytes(b'changed')
        self.assertIsNone(u.cached(self.root, '0.7.0-beta.4'))

    def test_failed_preflight_preserves_previous_pointer(self):
        pointer = self.root / 'active.json'
        pointer.write_text('{"previous":"unchanged"}')
        with self.assertRaises(subprocess.CalledProcessError):
            self.install(side_effect=subprocess.CalledProcessError(1, 'self-check'))
        self.assertEqual(json.loads(pointer.read_text()), {'previous': 'unchanged'})
        self.assertFalse((self.root / self.number).exists())
        self.assertFalse(list(self.root.glob('staging-*')))

    def test_checksum_mismatch_never_runs_download(self):
        self.manifest['assets'][self.name]['sha256'] = '0' * 64
        with patch.object(u.subprocess, 'run') as execute:
            with self.assertRaises(ValueError): self.install()
            execute.assert_not_called()
        self.assertFalse((self.root / 'active.json').exists())

    def test_zip_paths_cannot_escape_or_alias_windows_files(self):
        for name in ('ProjectAura/../../outside', '/ProjectAura/evil', 'ProjectAura/C:evil',
                     'ProjectAura/CON.txt', 'ProjectAura/a.', 'ProjectAura/./ProjectAura.exe',
                     'ProjectAura/PROJECTAURA.EXE', 'ProjectAura/back\\..\\..\\evil'):
            with self.subTest(name=name):
                path = self.root / 'bad.zip'
                path.write_bytes(archive_bytes((name, b'bad')))
                with self.assertRaises(ValueError): u.extract(path, self.root / 'out')
                self.assertFalse((self.root / 'out').exists())

    def test_corrupt_settings_disable_checks_and_bad_pointer_is_ignored(self):
        self.assertTrue(u.enabled(self.root))
        (self.root / 'settings.json').write_text('{')
        self.assertFalse(u.enabled(self.root))
        (self.root / 'active.json').write_text('{"version":"../elsewhere"}')
        self.assertIsNone(u.cached(self.root))

    def test_cancelled_download_does_not_activate(self):
        cancel = threading.Event()
        cancel.set()
        with patch.object(u, 'remote_json', return_value=self.manifest), \
             patch.object(u, 'request', return_value=io.BytesIO(self.data)):
            with self.assertRaises(ValueError):
                u.install(self.release, self.root, cancel, [''])
        self.assertFalse((self.root / 'active.json').exists())

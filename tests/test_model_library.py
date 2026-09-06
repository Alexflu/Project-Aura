import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aura.core import AuraError
from aura.model_library import ModelLibrary, REFERENCE


class ModelLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.profile = Path(self.temp.name) / 'state.db'
        self.library = ModelLibrary(self.profile)

    def test_import_survives_restart_and_deduplicates(self):
        key, model = self.library.import_model(REFERENCE)
        repeated, _ = self.library.import_model(REFERENCE)
        self.assertEqual(key, repeated)
        restored = ModelLibrary(self.profile)
        self.assertEqual(restored.selected, key)
        self.assertEqual(restored.restore().data, model.data)
        self.assertEqual(len(restored.entries()), 3)
        restored.choose(None)
        self.assertIsNone(ModelLibrary(self.profile).restore())
        self.assertTrue(self.library.path_for(key).exists())

    def test_reference_selection_persists(self):
        self.library.choose('@reference')
        self.assertIsNotNone(ModelLibrary(self.profile).restore())

    def test_missing_and_corrupt_pack_recover_without_deleting_selection(self):
        key, _ = self.library.import_model(REFERENCE)
        path = self.library.path_for(key)
        saved = self.library.settings.read_bytes()
        path.write_text('{}')
        restored = ModelLibrary(self.profile)
        self.assertIsNone(restored.restore())
        self.assertTrue(restored.warning)
        self.assertEqual(restored.settings.read_bytes(), saved)
        path.unlink()
        self.assertIsNone(ModelLibrary(self.profile).restore())

    def test_tampered_asset_is_revalidated_before_selection(self):
        key, model = self.library.import_model(REFERENCE)
        self.library.choose(None)
        path = self.library.path_for(key).parent / model.data['layers'][0]['asset']
        path.write_bytes(b'broken image')
        with self.assertRaises(AuraError):
            self.library.choose(key)
        self.assertIsNone(self.library.selected)
        self.assertIsNone(ModelLibrary(self.profile).selected)

    def test_untrusted_selection_cannot_choose_external_manifest(self):
        for value in ('../outside', str(REFERENCE), [], 12):
            with self.subTest(value=value):
                self.library.settings.write_text(json.dumps({'schema': 1, 'selected': value}))
                restored = ModelLibrary(self.profile)
                self.assertIsNone(restored.restore())
                self.assertTrue(restored.warning)

    def test_invalid_preferences_are_preserved_until_explicit_selection(self):
        for content in ('{', 'null', '{"schema":2,"selected":null}', 'x' * 1025):
            self.library.settings.write_text(content)
            restored = ModelLibrary(self.profile)
            self.assertIsNone(restored.restore())
            self.assertTrue(restored.warning)
            self.assertEqual(restored.settings.read_text(), content)

    def test_failed_save_preserves_previous_selection_and_cleans_temporary_file(self):
        self.library.choose('@reference')
        before = self.library.settings.read_bytes()
        with patch.object(Path, 'replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                self.library.choose(None)
        self.assertEqual(self.library.selected, '@reference')
        self.assertEqual(self.library.settings.read_bytes(), before)
        self.assertEqual(list(self.profile.parent.glob('.model-*.tmp')), [])


if __name__ == '__main__':
    unittest.main()

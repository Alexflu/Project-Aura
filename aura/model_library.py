"""Local model selection; packs are revalidated before they reach the renderer."""
import json
import re
from pathlib import Path
import tempfile

from .core import AuraError
from .models import import_pack, load_pack

REFERENCE = Path(__file__).with_name('assets') / 'rig-reference' / 'model.json'
PACK_ID = re.compile(r'[a-z][a-z0-9_.-]{2,63}-[a-f0-9]{16}')


class ModelLibrary:
    def __init__(self, profile):
        self.directory = Path(profile).with_suffix('.models')
        self.settings = Path(profile).with_suffix('.model.json')
        self.selected = None
        self.warning = ''
        try:
            if self.settings.exists():
                if self.settings.stat().st_size > 1024:
                    raise AuraError('Saved model selection is too large.')
                data = json.loads(self.settings.read_text(encoding='utf-8'))
                if not isinstance(data, dict) or set(data) != {'schema', 'selected'} or data['schema'] != 1:
                    raise AuraError('Invalid saved model selection.')
                self.path_for(data['selected'])
                self.selected = data['selected']
        except (OSError, ValueError, AuraError):
            self.warning = 'Saved model selection could not be read. Using default Aura; your packs are retained.'

    def path_for(self, key):
        if key is None:
            return None
        if key == '@reference':
            return REFERENCE
        if not isinstance(key, str) or not PACK_ID.fullmatch(key):
            raise AuraError('Choose a model from the local library.')
        folder = self.directory / key
        path = folder / 'model.json'
        if folder.resolve().parent != self.directory.resolve() or path.resolve().parent != folder.resolve():
            raise AuraError('Model library links must stay inside their pack.')
        return path

    def restore(self):
        try:
            path = self.path_for(self.selected)
            return load_pack(path)[0] if path else None
        except (OSError, ValueError, AuraError):
            self.warning = 'The selected model is missing or invalid. Using default Aura; choose another in Models.'
            self.selected = None
            return None

    def choose(self, key):
        path = self.path_for(key)
        model = load_pack(path)[0] if path else None
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.settings.parent,
                                             prefix='.model-', suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                json.dump({'schema': 1, 'selected': key}, output)
            temporary.replace(self.settings)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self.selected = key
        self.warning = ''
        return model

    def import_model(self, path):
        copied, _ = import_pack(path, self.directory)
        key = copied.parent.name
        return key, self.choose(key)

    def entries(self):
        """Read bounded labels only; selecting a row validates every declared asset."""
        result = [(None, 'Default Aura'), ('@reference', 'Reference rig')]
        if not self.directory.exists():
            return result
        for folder in sorted(self.directory.iterdir()):
            if len(result) >= 130:
                break
            if not PACK_ID.fullmatch(folder.name):
                continue
            try:
                path = self.path_for(folder.name)
                if path.stat().st_size > 65536:
                    continue
                data = json.loads(path.read_text(encoding='utf-8'))
                name = data.get('name') if isinstance(data, dict) else None
                if not isinstance(name, str) or not name.isprintable() or not 1 <= len(name) <= 80:
                    continue
                result.append((folder.name, name + ' · ' + folder.name[-8:]))
            except (OSError, ValueError, AuraError):
                continue
        return result

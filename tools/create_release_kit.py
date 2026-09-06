"""Prepare reviewable release assets locally; does not publish or configure funding."""
import hashlib
import json
from pathlib import Path
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura import __version__

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'

def main():
    source=OUT/f'ProjectAura-{__version__}-source.zip'
    folders=('aura','docs','examples','tests','tools','third_party','.github')
    files=[ROOT/name for name in ('README.md','LICENSE','CONTRIBUTING.md','THIRD_PARTY_NOTICES.md',
                                  'run_aura.py','launch_desktop.py','launch_mcp.py','.gitignore')]
    files+=list(ROOT.glob('requirements-*.txt'))
    for folder in folders:
        files += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.db','.sqlite3','.log')]
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):archive.write(path,Path('ProjectAura-source')/path.relative_to(ROOT))
    release=[OUT/f'ProjectAura-{__version__}-windows-x64.zip',source,OUT/'ProjectAura-0.6-demo.mp4',
             OUT/'ProjectAura-0.6-demo.srt',OUT/'ProjectAura-0.6-demo.png']
    checks={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in release}
    (OUT/'release-manifest.json').write_text(json.dumps(dict(version=__version__,published=False,assets=checks),indent=2),encoding='utf-8')
    notes=OUT/'RELEASE-NOTES.md'
    notes.write_text((ROOT/'docs/release-0.7.md').read_text(encoding='utf-8')+'\n\n## Prepared assets\n\nWindows portable beta, contributor source ZIP, 64-second MP4, captions, poster and SHA-256 manifest. These are local release candidates; this script does not publish them to GitHub or set up donations.\n',encoding='utf-8')
    kit=OUT/f'ProjectAura-{__version__}-release-kit.zip'
    with zipfile.ZipFile(kit,'w',zipfile.ZIP_STORED) as archive:
        for path in release+[notes,OUT/'release-manifest.json']:archive.write(path,path.name)
    print(json.dumps(dict(kit=str(kit),assets=checks)))

if __name__=='__main__':main()

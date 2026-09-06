"""Read an explicit source allowlist for connected GitHub object publication.

No credentials, profiles, build output or synced project references are included.
This helper only reads local files; it does not publish anything.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def files():
    roots = ('README.md', 'LICENSE', 'CONTRIBUTING.md', 'THIRD_PARTY_NOTICES.md',
             'run_aura.py', 'launch_desktop.py', 'launch_mcp.py', '.gitignore')
    result = [ROOT / name for name in roots]
    result += list(ROOT.glob('requirements-*.txt'))
    for folder in ('aura', 'docs', 'examples', 'tests', 'tools', 'third_party', '.github'):
        result += [p for p in (ROOT / folder).rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts
                   and p.suffix.lower() in ('.py', '.md', '.txt', '.json', '.yml', '.yaml', '.png', '.wav')]
    for path in result:
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError('Source links must remain inside the repository')
    return sorted(result)


def main():
    paths = files()
    if len(sys.argv) == 1:
        result = []
        for p in paths:
            data = p.read_bytes()
            result.append(dict(path=p.relative_to(ROOT).as_posix(), size=len(data),
                               binary=p.suffix.lower() in ('.png', '.wav'),
                               sha=hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()))
        print(json.dumps(result))
    else:
        data = paths[int(sys.argv[1])].read_bytes()
        if len(sys.argv) > 2:
            offset = int(sys.argv[2])
            print(base64.b64encode(data[offset:offset + 65535]).decode())
        else:
            print(json.dumps(data.decode('utf-8')))


if __name__ == '__main__':
    main()


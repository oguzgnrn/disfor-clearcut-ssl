"""Read-only integrity check for a delivery ZIP; safe to run before extraction."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import zipfile


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive entries')
        for name in names:
            parts = PurePosixPath(name).parts
            if '\\' in name or not parts or parts[0] != 'Orman_SSL' or '..' in parts or name.startswith('/'):
                raise ValueError('Unsafe archive path: ' + name)
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        manifest = json.loads(archive.read('Orman_SSL/PACKAGE_MANIFEST.json'))
        expected = set()
        for row in manifest:
            name = 'Orman_SSL/' + row['path']
            if name in expected:
                raise ValueError('Duplicate manifest entry')
            expected.add(name)
            payload = archive.read(name)
            if len(payload) != row['bytes'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
                raise ValueError('File hash or length mismatch: ' + row['path'])
        allowed = expected | {'Orman_SSL/PACKAGE_MANIFEST.json', 'Orman_SSL/SUNUM_PAKETI.txt'}
        if set(names) - allowed:
            raise ValueError('Unlisted archive payload')
    return dict(status='passed', files=len(manifest), checks=['safe paths','unique entries','CRC','all SHA-256 hashes','manifest coverage'])

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    args=parser.parse_args()
    try:
        print(json.dumps(verify(args.archive),indent=2))
    except (ValueError,KeyError,zipfile.BadZipFile) as exc:
        parser.error(str(exc))

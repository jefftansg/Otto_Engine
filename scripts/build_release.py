"""Build a reproducible, tracked-source ZIP and SHA-256 inventory from HEAD."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile


def build_release(root, destination=None):
    root = Path(root)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    commit = git('rev-parse', 'HEAD').decode().strip()
    version = git('show', 'HEAD:VERSION').decode().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?', version):
        raise ValueError('Invalid committed VERSION.')
    prefix = 'Otto_Engine_v'+version
    destination = Path(destination or root.parent/(prefix+'.zip'))
    stamp = datetime.fromtimestamp(int(git('show', '-s', '--format=%ct', 'HEAD')), timezone.utc)
    timestamp = stamp.timetuple()[:6]
    files = {}
    with tarfile.open(fileobj=io.BytesIO(git('archive', '--format=tar', 'HEAD'))) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            name = member.name
            if name.startswith('/') or '..' in Path(name).parts:
                raise ValueError('Unsafe committed source path: '+name)
            files[name] = (archive.extractfile(member).read(), member.mode)
    for name in ('QUICK_START_v'+version+'.md', 'RELEASE_NOTES_v'+version+'.md', 'constraints-m0.txt'):
        if name not in files:
            raise ValueError('Release is missing '+name)
    manifest = dict(version=version, source_commit=commit, files=[
        dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest())
        for name,(data,_) in sorted(files.items())])
    files['SOURCE_MANIFEST.json'] = ((json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode(), 0o644)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name,(data,mode) in sorted(files.items()):
            info = zipfile.ZipInfo(prefix+'/'+name, timestamp)
            info.create_system = 3
            info.external_attr = (0o100755 if mode & 0o111 else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError('Release ZIP integrity check failed.')
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(destination.suffix+'.sha256').write_text(digest+'  '+destination.name+'\n')
    return destination, digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    path, digest = build_release(Path(__file__).resolve().parents[1], args.output)
    print(str(path))
    print('SHA-256 '+digest)

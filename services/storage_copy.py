"""Runs in an isolated helper with only the source and destination mounted."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys


def inventory(source, destination):
    if not source.is_dir() or not destination.is_dir():
        raise ValueError('Begge mapper skal findes på serveren.')
    if os.path.samefile(source, destination):
        raise ValueError('Kilde og destination er samme mappe.')
    if any(destination.iterdir()):
        raise ValueError('Den nye mappe skal være tom. Eksisterende filer overskrives ikke.')
    entries, total = [], 0
    dest_stat = destination.stat()
    for root, dirs, files in os.walk(source, followlinks=False):
        for name in dirs + files:
            path = Path(root) / name
            info = path.lstat()
            if (info.st_dev, info.st_ino) == (dest_stat.st_dev, dest_stat.st_ino):
                raise ValueError('Den nye mappe må ikke ligge inde i den gamle.')
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                raise ValueError('Mappen indeholder en særlig filtype, som skal flyttes manuelt.')
            entries.append((path.relative_to(source), info))
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
    free = shutil.disk_usage(destination).free
    if free < total + 256 * 1024**2:
        raise ValueError('Der er ikke plads nok på destinationen til en komplet kopi.')
    return entries, total, free


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').digest()


def transfer(source, destination, check_only=False):
    entries, total, free = inventory(source, destination)
    if check_only:
        return {'bytes': total, 'free_bytes': free, 'entries': len(entries)}
    # No merging, deleting or following symlinks. The old directory is retained.
    for relative, info in entries:
        old, new = source / relative, destination / relative
        if stat.S_ISLNK(info.st_mode):
            new.symlink_to(os.readlink(old))
        elif stat.S_ISDIR(info.st_mode):
            new.mkdir()
        else:
            with old.open('rb') as inp, new.open('xb') as out:
                shutil.copyfileobj(inp, out, length=1024**2)
                out.flush()
                os.fsync(out.fileno())
            if digest(old) != digest(new):
                raise ValueError('Kontrol af filkopien fejlede. Den gamle placering er bevaret.')
        if hasattr(os, 'chown'):
            os.chown(new, info.st_uid, info.st_gid, follow_symlinks=False)
        shutil.copystat(old, new, follow_symlinks=False)
    # Directory timestamps/permissions are restored after their children are copied.
    for relative, info in reversed(entries):
        if stat.S_ISDIR(info.st_mode):
            shutil.copystat(source / relative, destination / relative)
    info = source.stat()
    if hasattr(os, 'chown'):
        os.chown(destination, info.st_uid, info.st_gid)
    shutil.copystat(source, destination)
    return {'bytes': total, 'entries': len(entries)}


if __name__ == '__main__':
    try:
        print(json.dumps(transfer(Path('/source'), Path('/destination'), sys.argv[1] == 'check')))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)

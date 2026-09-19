"""Runs in an isolated helper with only the source and destination mounted."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time

MANIFEST = '.fjordhub-storage-transfer.json'


def identity(path):
    info = path.lstat()
    return [info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns]


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


def digest(path, progress=None):
    with path.open('rb') as stream:
        checksum = hashlib.sha256()
        while block := stream.read(1024**2):
            checksum.update(block)
            if progress:
                progress(len(block))
        return checksum.digest()


def transfer(source, destination, check_only=False, prepare_move=False, progress=None):
    entries, total, free = inventory(source, destination)
    if check_only:
        return {'bytes': total, 'free_bytes': free, 'entries': len(entries)}
    if prepare_move and any(relative.parts[0] == MANIFEST for relative, _ in entries):
        raise ValueError('En tidligere flytning skal kontrolleres først.')
    manifest = {'source': identity(source)[:2], 'destination': identity(destination)[:2], 'entries': []}
    copied, checked = 0, 0
    def report(phase):
        if progress:
            progress({'phase':phase, 'completed_bytes':copied + checked, 'total_bytes':total * 3,
                      'copied_bytes':copied, 'data_bytes':total})
    def verified(count):
        nonlocal checked
        checked += count
        report('Kontrollerer filkopien')
    report('Kopierer filer')
    # No merging, deleting or following symlinks during the copy.
    for relative, info in entries:
        old, new = source / relative, destination / relative
        before = identity(old)
        record = {'path': relative.as_posix(), 'identity': before}
        if prepare_move and info.st_dev != source.stat().st_dev:
            raise ValueError('Kildemappen indeholder et andet monteret filsystem. Flyt det separat.')
        if stat.S_ISLNK(info.st_mode):
            new.symlink_to(os.readlink(old))
            record['link'] = os.readlink(old)
        elif stat.S_ISDIR(info.st_mode):
            new.mkdir()
        else:
            with old.open('rb') as inp, new.open('xb') as out:
                while block := inp.read(1024**2):
                    out.write(block)
                    copied += len(block)
                    report('Kopierer filer')
                out.flush()
                os.fsync(out.fileno())
            checksum = digest(old, verified)
            if checksum != digest(new, verified):
                raise ValueError('Kontrol af filkopien fejlede. Den gamle placering er bevaret.')
            record['sha256'] = checksum.hex()
        if identity(old) != before:
            raise ValueError('Kilden blev ændret under kopieringen. Originalerne bevares.')
        manifest['entries'].append(record)
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
    result = {'bytes': total, 'entries': len(entries)}
    if prepare_move:
        with (destination / MANIFEST).open('x', encoding='utf-8') as out:
            json.dump(manifest, out)
            out.flush()
            os.fsync(out.fileno())
        result['manifest_sha256'] = digest(destination / MANIFEST).hex()
    if hasattr(os, 'sync'):
        os.sync()
    return result


def cleanup(source, destination, expected_digest, progress=None):
    """Remove only the unchanged originals recorded by a verified copy.

    The destination may have been updated by the restarted app. The sealed
    manifest proves the copy was verified before activation. New or modified
    source files, missing targets and replaced parent directories stop cleanup.
    """
    manifest_path = destination / MANIFEST
    if manifest_path.is_symlink() or digest(manifest_path).hex() != expected_digest:
        raise ValueError('Flytningens kontrolfil mangler eller er ændret.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if identity(source)[:2] != manifest['source'] or identity(destination)[:2] != manifest['destination']:
        raise ValueError('En mappe er blevet udskiftet. Originalerne bevares.')
    records = manifest['entries']
    total = sum(r['identity'][3] for r in records if 'sha256' in r)
    checked = 0
    def verified(count):
        nonlocal checked
        checked += count
        if progress:
            progress({'phase':'Kontrollerer originaler før sletning', 'completed_bytes':checked, 'total_bytes':total})
    expected = {r['path'] for r in records}
    actual = {p.relative_to(source).as_posix() for root, dirs, files in os.walk(source, followlinks=False)
              for p in (Path(root) / name for name in dirs + files)}
    if actual != expected:
        raise ValueError('Kildens indhold er ændret. Originalerne bevares.')

    def validate(record, check_contents=True):
        relative = Path(record['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Ugyldig sti i kontrolfilen.')
        old, new = source / relative, destination / relative
        for parent in relative.parents:
            if (source / parent).is_symlink() or (destination / parent).is_symlink():
                raise ValueError('En overmappe er ændret til et link.')
        original = record['identity']
        directory = stat.S_ISDIR(original[2])
        current = identity(old)
        # Removing children changes directory timestamps and sizes.
        if (current[:3] if directory else current) != (original[:3] if directory else original):
            raise ValueError('En original er ændret. Oprydningen er afbrudt.')
        if stat.S_IFMT(new.lstat().st_mode) != stat.S_IFMT(original[2]):
            raise ValueError('En fil mangler eller har ændret type på destinationen.')
        if check_contents and 'sha256' in record and digest(old, verified).hex() != record['sha256']:
            raise ValueError('En original er ændret. Oprydningen er afbrudt.')
        if 'link' in record and (os.readlink(old) != record['link'] or os.readlink(new) != record['link']):
            raise ValueError('Et link er ændret. Oprydningen er afbrudt.')
        return old, directory

    # Validate the entire source before deleting anything; never use rmtree.
    for record in records:
        validate(record)
    if progress:
        progress({'phase':'Fjerner kontrollerede originaler'})
    for record in reversed(records):
        old, directory = validate(record, check_contents=False)
        if directory:
            old.rmdir()
        else:
            old.unlink()
    if any(source.iterdir()):
        raise ValueError('Der er nye filer i kildemappen. De er bevaret.')
    manifest_path.unlink()
    return {'removed': len(records)}


if __name__ == '__main__':
    try:
        last_report = [0, None]
        def report(value):
            now = time.monotonic()
            if now - last_report[0] >= 1 or value['phase'] != last_report[1] or value.get('completed_bytes') == value.get('total_bytes'):
                print(json.dumps({'progress':value}), flush=True)
                last_report[:] = [now, value['phase']]
        source, destination = Path('/source'), Path('/destination')
        mode = sys.argv[1]
        result = cleanup(source, destination, sys.argv[2], progress=report) if mode == 'cleanup' else transfer(
            source, destination, mode == 'check', prepare_move=mode == 'prepare-move', progress=report)
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)

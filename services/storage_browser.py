"""Directory-only operations inside a scoped Docker helper."""
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys

ROOTS = ('/mnt', '/media', '/srv', '/opt', '/home')


def checked(root, value):
    if not isinstance(value, str) or not any(value == p or value.startswith(p + '/') for p in ROOTS):
        raise ValueError('Vælg en mappe under /mnt, /media, /srv, /opt eller /home.')
    parts = PurePosixPath(value).parts[1:]
    if '..' in parts or len(value) > 1024:
        raise ValueError('Ugyldig mappesti.')
    result = root
    for part in parts:
        result = result / part
        if result.is_symlink():
            raise ValueError('Links kan ikke bruges som filplacering.')
    return result


def browse(root, value):
    if not value:
        return {'path': '', 'parent': None, 'directories': [
            {'name': p, 'path': p} for p in ROOTS if (root / p[1:]).is_dir() and not (root / p[1:]).is_symlink()]}
    directory = checked(root, value)
    if not directory.is_dir():
        raise ValueError('Mappen findes ikke på Docker-serveren.')
    directories = []
    truncated = False
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False) and not entry.name.startswith('.'):
                if len(directories) == 500:
                    truncated = True
                    break
                directories.append({'name': entry.name, 'path': value.rstrip('/') + '/' + entry.name})
    return {'path': value, 'parent': '' if value in ROOTS else str(PurePosixPath(value).parent),
            'directories': sorted(directories, key=lambda r: r['name'].lower()),
            'free_bytes': shutil.disk_usage(directory).free, 'truncated': truncated}


def probe(root, value):
    directory = checked(root, value)
    ancestor = directory
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not ancestor.is_dir() or ancestor == root:
        raise ValueError('Den overordnede mappe skal findes på serveren.')
    return {'ancestor': '/' + ancestor.relative_to(root).as_posix(),
            'relative': directory.relative_to(ancestor).as_posix()}


def create(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Ugyldig mappesti.')
    # Hold directory descriptors and never follow links, including during races.
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in Path(relative).parts:
            try:
                os.mkdir(part, mode=0o755, dir_fd=fd)
            except FileExistsError:
                pass
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
    finally:
        os.close(fd)
    return {'created': True}


if __name__ == '__main__':
    try:
        action, value = sys.argv[1:3]
        result = create(Path('/folder'), value) if action == 'create' else (
            probe(Path('/host'), value) if action == 'probe' else browse(Path('/host'), value))
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({'error': str(exc) if isinstance(exc, ValueError) else 'Mappen kunne ikke læses eller oprettes. Kontrollér sti og rettigheder.'}))
        sys.exit(1)

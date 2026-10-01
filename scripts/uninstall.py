#!/usr/bin/env python3
"""Remove FjordHub's Docker runtime from its host, preserving all storage."""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.uninstaller import remove_runtime


def main():
    parser = argparse.ArgumentParser(description='Afinstallér FjordHubs Docker-runtime. Mapper, mounts og Docker-volumes bevares.')
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1],
                        help='FjordHubs eksisterende Compose-mappe')
    args = parser.parse_args()
    try:
        remove_runtime({'container_name': 'fjordhub'}, args.directory, required_service='fjordhub')
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        message = str(exc) if isinstance(exc, RuntimeError) else 'Afinstallationen fejlede. Data er bevaret; kontrollér Docker.'
        parser.exit(1, message + '\n')
    print('FjordHubs runtime er fjernet. Mediefiler, mounts, Docker-volumes, appmapper og indstillinger er bevaret. LXC-containeren er ikke slettet.')


if __name__ == '__main__':
    main()

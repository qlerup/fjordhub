"""Byg FjordHub-pakker fra packages_src/ til packages_src/dist/.

Kørsel:  python scripts/build_packages.py
Udskriver sha256 for hver zip, som skal ind i BUILTIN_PACKAGES i app.py.
Zippene uploades til en GitHub-release med tagget packages-v<version>.
"""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages_src"
DIST = SRC / "dist"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for pkg_dir in sorted(p for p in SRC.iterdir() if p.is_dir() and p.name != "dist"):
        manifest = json.loads((pkg_dir / "manifest.json").read_text(encoding="utf-8"))
        out = DIST / f"{pkg_dir.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as bundle:
            for file in sorted(pkg_dir.iterdir()):
                if file.is_file():
                    bundle.write(file, file.name)
        sha = hashlib.sha256(out.read_bytes()).hexdigest()
        print(f"{pkg_dir.name} v{manifest.get('version')}")
        print(f"  fil:    {out.relative_to(ROOT)}")
        print(f"  sha256: {sha}")


if __name__ == "__main__":
    main()

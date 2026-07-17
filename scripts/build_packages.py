"""Byg FjordHub-pakker fra packages_src/ til packages_src/dist/.

Kørsel:  python scripts/build_packages.py

Bygger zips, beregner sha256 og opdaterer packages_catalog.json automatisk
(version, download_url og sha256 pr. pakke). Hub'en henter kataloget ved
runtime, så en pakke-opdatering kræver IKKE redeploy af hub'en:

  1. Ret pakken i packages_src/<id>/ og bump "version" i manifest.json
  2. python scripts/build_packages.py
  3. gh release create packages-v<version> packages_src/dist/<id>.zip
  4. git commit + push (packages_catalog.json)
  → Butikken viser en Opdatér-knap på kortet.
"""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages_src"
DIST = SRC / "dist"
CATALOG = ROOT / "packages_catalog.json"
RELEASE_URL = "https://github.com/qlerup/fjordhub/releases/download/packages-v{version}/{name}.zip"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in catalog.get("packages", [])}
    release_files: dict[str, list[str]] = {}

    for pkg_dir in sorted(p for p in SRC.iterdir() if p.is_dir() and p.name != "dist"):
        manifest = json.loads((pkg_dir / "manifest.json").read_text(encoding="utf-8"))
        package_id = manifest["id"]
        version = str(manifest.get("version"))
        out = DIST / f"{pkg_dir.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as bundle:
            for file in sorted(pkg_dir.iterdir()):
                if file.is_file():
                    bundle.write(file, file.name)
        sha = hashlib.sha256(out.read_bytes()).hexdigest()

        entry = entries.setdefault(package_id, {"id": package_id, "name": manifest.get("name", package_id)})
        entry["version"] = version
        entry["download_url"] = RELEASE_URL.format(version=version, name=pkg_dir.name)
        entry["sha256"] = sha
        release_files.setdefault(version, []).append(str(out.relative_to(ROOT)).replace("\\", "/"))

        print(f"{package_id} v{version}  sha256={sha}")

    catalog["packages"] = list(entries.values())
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\npackages_catalog.json opdateret.")
    for version, files in sorted(release_files.items()):
        print(f"Upload til GitHub (hvis release ikke findes endnu):")
        print(f"  gh release create packages-v{version} {' '.join(files)} --title \"FjordHub-pakker v{version}\" --notes \"Pakkeopdatering\"")
        print(f"  (findes releasen: gh release upload packages-v{version} {' '.join(files)} --clobber)")


if __name__ == "__main__":
    main()

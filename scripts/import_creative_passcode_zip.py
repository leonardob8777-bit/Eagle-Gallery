#!/usr/bin/env python3
"""Publish the thirteen standalone digit styles from the owner's asset ZIP."""

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalogs/passcode-v1.json"
PACKAGES = ROOT / "passcode/packages"
PREVIEWS = ROOT / "previews/passcode/creative-v1"
BASE = "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/"
SOURCE_ROOT = "EaglePasscode_Numeros_Creativos/"
NAMES = {
    "01_enredadera": "Enredadera",
    "02_bordado": "Bordado",
    "03_cuerda": "Cuerda",
    "04_constelacion": "Constelación",
    "05_cerillas": "Cerillas",
    "06_circuito": "Circuito",
    "07_fideos": "Fideos",
    "08_huesos": "Huesos",
    "09_vitral": "Vitral",
    "10_galaxia": "Galaxia",
    "11_origami": "Origami",
    "12_cinta_washi": "Cinta washi",
    "13_plastilina": "Plastilina",
}


def png(archive: ZipFile, name: str, size: tuple[int, int], transparent: bool) -> bytes:
    data = archive.read(name)
    with Image.open(BytesIO(data)) as image:
        image.load()
        assert image.format == "PNG" and image.size == size, name
        if transparent:
            assert image.mode == "RGBA" and image.getchannel("A").getextrema()[0] < 255, name
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    args = parser.parse_args()

    manifest = json.loads(CATALOG.read_text())
    themes = manifest["themes"]
    assert manifest["schemaVersion"] == 1
    existing_ids = {theme["id"] for theme in themes}
    assert len(existing_ids) == len(themes)

    with ZipFile(args.source_zip) as archive:
        assert archive.testzip() is None, "source ZIP is corrupt"
        folders = {
            match.group(1)
            for name in archive.namelist()
            if (match := re.fullmatch(re.escape(SOURCE_ROOT) + r"([^/]+)/0\.png", name))
        }
        assert folders == set(NAMES), (folders, set(NAMES))

        for folder, title in NAMES.items():
            slug = re.sub(r"^\d+_", "", folder).replace("_", "-")
            identifier = f"creative-{slug}"
            assert identifier not in existing_ids, identifier
            prefix = SOURCE_ROOT + folder + "/"
            digits = {
                digit: png(archive, prefix + digit + ".png", (256, 256), True)
                for digit in "0123456789"
            }
            reference = png(archive, prefix + "referencia.png", (1170, 2532), False)

            PACKAGES.mkdir(parents=True, exist_ok=True)
            PREVIEWS.mkdir(parents=True, exist_ok=True)
            package = PACKAGES / f"{identifier}-v1.passthm"
            with ZipFile(package, "w", compression=ZIP_DEFLATED, compresslevel=9) as output:
                for digit, data in digits.items():
                    entry = ZipInfo(digit + ".png", date_time=(2026, 10, 31, 0, 0, 0))
                    entry.compress_type = ZIP_DEFLATED
                    output.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=9)
            (PREVIEWS / f"{identifier}.png").write_bytes(reference)
            themes.append({
                "id": identifier,
                "name": title,
                "description": "Números creativos para el código. Incluye los dígitos; no incluye fondo.",
                "authors": "Eagle",
                "version": "1",
                "preview": BASE + f"previews/passcode/creative-v1/{identifier}.png",
                "url": BASE + f"passcode/packages/{package.name}",
                "byteCount": package.stat().st_size,
                "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            })
            print(identifier, package.stat().st_size)

    CATALOG.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

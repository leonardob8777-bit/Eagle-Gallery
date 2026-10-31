#!/usr/bin/env python3
"""Import the owner's layered static Passcode artwork into Eagle's online catalogs.

The supplied ZIP is an asset source, not an instruction file. This script only
accepts the nine existing catalog IDs and their exact image deliverables.
"""

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from prepare_passcode_wallpapers import ROOT, WIDTH, HEIGHT, build_package


PASSCODE_CATALOG = ROOT / "catalogs/passcode-v1.json"
WALLPAPER_CATALOG = ROOT / "catalogs/wallpaper-v1.json"
PASSCODE_PACKAGES = ROOT / "passcode/packages"
PASSCODE_PREVIEWS = ROOT / "previews/passcode/applicable"
WALLPAPER_PREVIEWS = ROOT / "previews/wallpapers"
FOREGROUND_PREVIEWS = WALLPAPER_PREVIEWS / "foreground"
BASE_URL = "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/"


def read_png(archive: ZipFile, path: str, size: tuple[int, int], alpha: bool) -> bytes:
    data = archive.read(path)
    with Image.open(BytesIO(data)) as image:
        image.load()
        assert image.format == "PNG" and image.size == size, path
        if alpha:
            assert image.mode in ("RGBA", "LA") and image.getchannel("A").getextrema()[0] < 255, path
    return data


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    args = parser.parse_args()
    passcode = json.loads(PASSCODE_CATALOG.read_text())
    wallpaper = json.loads(WALLPAPER_CATALOG.read_text())
    passcode_by_id = {item["id"]: item for item in passcode["themes"]}
    wallpaper_by_id = {item["id"]: item for item in wallpaper["wallpapers"]}
    assert len(passcode_by_id) == len(wallpaper_by_id) == 9
    assert set(passcode_by_id) == set(wallpaper_by_id)
    PASSCODE_PACKAGES.mkdir(parents=True, exist_ok=True)
    PASSCODE_PREVIEWS.mkdir(parents=True, exist_ok=True)
    WALLPAPER_PREVIEWS.mkdir(parents=True, exist_ok=True)
    FOREGROUND_PREVIEWS.mkdir(parents=True, exist_ok=True)

    with ZipFile(args.source_zip) as archive:
        assert archive.testzip() is None, "source ZIP is corrupt"
        names = set(archive.namelist())
        source_ids = {
            match.group(1)
            for name in names
            if (match := re.fullmatch(r"EaglePasscode_Estaticos/([^/]+)/fondo\.png", name))
        }
        assert source_ids == set(passcode_by_id), (source_ids, set(passcode_by_id))

        for identifier in sorted(source_ids):
            prefix = f"EaglePasscode_Estaticos/{identifier}/"
            background = read_png(archive, prefix + "fondo.png", (WIDTH, HEIGHT), False)
            foreground = read_png(archive, prefix + "primer_plano.png", (WIDTH, HEIGHT), True)
            reference = read_png(archive, prefix + "referencia.png", (WIDTH, HEIGHT), False)
            digits = {
                digit: read_png(archive, prefix + digit + ".png", (256, 256), True)
                for digit in "0123456789"
            }

            passcode_package = PASSCODE_PACKAGES / f"{identifier}-v2.passthm"
            with ZipFile(passcode_package, "w", compression=ZIP_DEFLATED, compresslevel=9) as result:
                for digit, data in digits.items():
                    result.writestr(digit + ".png", data)
            PASSCODE_PREVIEWS.joinpath(identifier + ".png").write_bytes(reference)

            with Image.open(BytesIO(background)) as image:
                wallpaper_package = build_package(
                    identifier,
                    wallpaper_by_id[identifier]["name"],
                    image,
                    foreground_png=foreground,
                    version=2,
                )
            WALLPAPER_PREVIEWS.joinpath(identifier + ".png").write_bytes(background)
            FOREGROUND_PREVIEWS.joinpath(identifier + ".png").write_bytes(foreground)

            item = passcode_by_id[identifier]
            item.update({
                "preview": BASE_URL + f"previews/passcode/applicable/{identifier}.png",
                "description": "Diseño completo de referencia. Instala los números y el fondo a juego por separado.",
                "wallpaperID": identifier,
                "url": BASE_URL + f"passcode/packages/{passcode_package.name}",
                "byteCount": passcode_package.stat().st_size,
                "sha256": digest(passcode_package.read_bytes()),
                "version": "2",
            })
            item = wallpaper_by_id[identifier]
            item.update({
                "preview": BASE_URL + f"previews/wallpapers/{identifier}.png",
                "foregroundPreview": BASE_URL + f"previews/wallpapers/foreground/{identifier}.png",
                "foregroundByteCount": len(foreground),
                "foregroundSha256": digest(foreground),
                "description": "Fondo de dos capas para el estilo Eagle. Los números se instalan por separado en Passcode.",
                "url": BASE_URL + f"wallpapers/packages/{wallpaper_package.name}",
                "byteCount": wallpaper_package.stat().st_size,
                "sha256": digest(wallpaper_package.read_bytes()),
            })
            print(identifier, passcode_package.stat().st_size, wallpaper_package.stat().st_size)

    PASSCODE_CATALOG.write_text(json.dumps(passcode, ensure_ascii=False, indent=2) + "\n")
    WALLPAPER_CATALOG.write_text(json.dumps(wallpaper, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

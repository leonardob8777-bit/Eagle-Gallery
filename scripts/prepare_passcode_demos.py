#!/usr/bin/env python3
"""Stage animated previews from the owner's EaglePasscodeThemes.zip.

These HTML previews are not .passthm packages and cannot be installed on the
system Passcode screen. The generated catalog entries are preview-only.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PREFIX = "EaglePasscodeThemes/"
RAW_BASE = "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    catalog_path = ROOT / "catalogs/passcode-v1.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert catalog["schemaVersion"] == 1
    assert not catalog["themes"], "catalog already contains entries; merge manually"

    with ZipFile(args.archive) as archive:
        infos = archive.infolist()
        assert len(infos) <= 100
        assert sum(info.file_size for info in infos) <= 50_000_000
        names = set(archive.namelist())
        manifest = json.loads(archive.read(SOURCE_PREFIX + "themes.json"))
        assert manifest.get("version") == 1
        themes = manifest.get("themes")
        assert isinstance(themes, list) and len(themes) <= 50
        runtime = archive.read(SOURCE_PREFIX + "themes/eagle-runtime.js").decode("utf-8")
        assert "</script" not in runtime.lower()

        entries = []
        for theme in themes:
            identifier = theme["id"]
            assert re.fullmatch(r"[a-z0-9-]{1,80}", identifier)
            assert theme["file"] == f"themes/{identifier}.html"
            html = archive.read(SOURCE_PREFIX + theme["file"]).decode("utf-8")
            assert html.count('<script src="./eagle-runtime.js"></script>') == 1
            html = html.replace(
                '<script src="./eagle-runtime.js"></script>',
                f"<script>\n{runtime}\n</script>",
            )
            # The preview has no access to the real passcode. Use local fonts
            # and stop the HTML from fetching other scripts, frames, or media.
            html = re.sub(
                r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^>]+>\s*',
                "",
                html,
            )
            csp = (
                '<meta http-equiv="Content-Security-Policy" '
                'content="default-src \'none\'; img-src data:; '
                'style-src \'unsafe-inline\'; '
                'script-src \'unsafe-inline\' \'unsafe-eval\'">'
            )
            html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n{csp}', 1)
            assert "fonts.googleapis.com" not in html
            html_bytes = html.encode("utf-8")
            preview_name = SOURCE_PREFIX + f"previews/{identifier}.png"
            assert preview_name in names
            preview = archive.read(preview_name)
            assert preview.startswith(b"\x89PNG\r\n\x1a\n")

            html_path = ROOT / "passcode/live" / f"{identifier}.html"
            preview_path = ROOT / "previews/passcode" / f"{identifier}.png"
            html_path.parent.mkdir(parents=True, exist_ok=True)
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_bytes(html_bytes)
            preview_path.write_bytes(preview)
            entries.append({
                "id": identifier,
                "name": theme["name"],
                "description": "",
                "authors": "Eagle",
                "version": "1",
                "preview": RAW_BASE + f"previews/passcode/{identifier}.png",
                "demoURL": RAW_BASE + f"passcode/live/{identifier}.html",
                "demoByteCount": len(html_bytes),
                "demoSha256": digest(html_bytes),
            })

    catalog["themes"] = entries
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(entries)} preview-only themes from {args.archive.name}")


if __name__ == "__main__":
    main()

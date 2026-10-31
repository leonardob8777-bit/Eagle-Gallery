#!/usr/bin/env python3
"""Validate Eagle's Passcode and Wallpapers manifests before publication."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PREFIX = "/leonardob8777-bit/Eagle-Gallery/main/previews/"
PACKAGE_PREFIX = "/leonardob8777-bit/Eagle-Gallery/releases/download/"


def check_entry(entry: dict, kind: str, packages: Path | None) -> None:
    identifier = entry.get("id")
    assert isinstance(identifier, str) and re.fullmatch(r"[a-z0-9-]{1,80}", identifier), identifier
    assert isinstance(entry.get("name"), str) and entry["name"].strip(), identifier
    assert isinstance(entry.get("description", ""), str), identifier
    digest = entry.get("sha256")
    assert isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), identifier
    size = entry.get("byteCount")
    limit = 50 * 1024 * 1024 if kind == "passcode" else 120 * 1024 * 1024
    assert isinstance(size, int) and not isinstance(size, bool) and 0 < size <= limit, identifier

    preview = urlparse(entry.get("preview", ""))
    assert preview.scheme == "https" and preview.netloc == "raw.githubusercontent.com", identifier
    assert preview.path.startswith(PREVIEW_PREFIX) and not preview.query, identifier
    preview_path = (ROOT / unquote(preview.path.removeprefix(
        "/leonardob8777-bit/Eagle-Gallery/main/"
    ))).resolve()
    assert preview_path.is_relative_to((ROOT / "previews").resolve()), identifier
    assert preview_path.is_file(), f"missing preview: {preview_path}"

    package = urlparse(entry.get("url", ""))
    assert package.scheme == "https" and package.netloc == "github.com", identifier
    assert package.path.startswith(PACKAGE_PREFIX) and not package.query, identifier
    extension = ".passthm" if kind == "passcode" else ".tendies"
    assert package.path.endswith(extension), identifier
    if packages is not None:
        local = packages / unquote(Path(package.path).name)
        assert local.is_file(), f"missing package: {local}"
        assert local.stat().st_size == size, f"size mismatch: {local}"
        with local.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        assert actual == digest, f"SHA-256 mismatch: {local}"

    if kind == "wallpaper":
        minimum = entry.get("minimumIOSMajor", 17)
        assert isinstance(minimum, int) and not isinstance(minimum, bool) and 16 <= minimum <= 26


def check_catalog(path: Path, key: str, kind: str, packages: Path | None) -> int:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest.get("schemaVersion") == 1, path
    entries = manifest.get(key)
    assert isinstance(entries, list) and len(entries) <= 1000, path
    identifiers: set[str] = set()
    for entry in entries:
        assert isinstance(entry, dict), path
        check_entry(entry, kind, packages)
        assert entry["id"] not in identifiers, f"duplicate ID: {entry['id']}"
        identifiers.add(entry["id"])
    print(f"PASS {path.name}: {len(entries)} entries")
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages-dir", type=Path)
    args = parser.parse_args()
    check_catalog(ROOT / "catalogs/passcode-v1.json", "themes", "passcode", args.packages_dir)
    check_catalog(ROOT / "catalogs/wallpaper-v1.json", "wallpapers", "wallpaper", args.packages_dir)


if __name__ == "__main__":
    main()

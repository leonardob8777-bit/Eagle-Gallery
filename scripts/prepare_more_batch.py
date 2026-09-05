#!/usr/bin/env python3
"""Prepare the mixed `more` batch without modifying source files or Dock geometry."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
import prepare_twigal_batch as batch


def source_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    batch.RELEASE = "https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v7"
    files = sorted(p for p in args.source.iterdir() if p.is_file() and not p.name.startswith("."))
    assert files
    old = json.loads((batch.REPO / "catalogs/dock-v1.json").read_text())
    known_hashes = set()
    for manifest_path in Path("/Users/leonardobaptiste/Documents/Codex/Eagle-Gallery-Builds").glob("*/manifest.json"):
        try:
            known_hashes.update(row["sourceSHA256"] for row in json.loads(manifest_path.read_text()))
        except (KeyError, TypeError, json.JSONDecodeError):
            pass
    jobs = []
    counts = {"static": 0, "live": 0}
    batch_hashes = set()
    for source in files:
        suffix = source.suffix.lower()
        assert suffix in (".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov"), source
        digest = source_digest(source)
        assert digest not in known_hashes and digest not in batch_hashes, f"duplicate: {source}"
        batch_hashes.add(digest)
        if suffix in (".mp4", ".mov"):
            kind = "live"
        else:
            with Image.open(source) as image:
                kind = "live" if getattr(image, "n_frames", 1) > 1 else "static"
        counts[kind] += 1
        number = counts[kind]
        jobs.append((source, f"more-{kind}-{number:03d}", f"Gallery {number:03d}"))

    def prepare(job):
        source, asset_id, title = job
        return batch.prepare(source, args.output, asset_id=asset_id, asset_title=title)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(prepare, jobs))
    themes = [result["theme"] for result in results]
    catalog = dict(old, themes=old["themes"] + themes)
    ids = [theme["id"] for theme in catalog["themes"]]
    assert len(ids) == len(set(ids))
    encoded = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    assert len(encoded.encode()) < 512 * 1024
    (args.output / "catalog.json").write_text(encoded)
    (args.output / "manifest.json").write_text(json.dumps(results, indent=2) + "\n")
    for start in range(0, len(results), 30):
        chunk = results[start:start + 30]
        sheet = Image.new("RGB", (1200, ((len(chunk) + 2) // 3) * 145), "#202020")
        draw = ImageDraw.Draw(sheet)
        for index, record in enumerate(chunk):
            x, y = index % 3 * 400, index // 3 * 145
            theme = record["theme"]
            with Image.open(args.output / "previews" / f"{theme['id']}.png") as preview:
                sheet.paste(preview.resize((382, 106)), (x + 8, y + 2))
            draw.text((x + 8, y + 113), f"{theme['id']}  {Path(record['source']).name}", fill="white")
        sheet.save(args.output / f"contact-{start // 30 + 1:02d}.jpg")
    assert all(source_digest(Path(row["source"])) == row["sourceSHA256"] for row in results)
    print(json.dumps({"total": len(catalog["themes"]), "added": len(results), **counts,
                      "originalsUnchanged": True}), flush=True)


if __name__ == "__main__":
    main()

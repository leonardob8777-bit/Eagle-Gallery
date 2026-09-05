#!/usr/bin/env python3
"""Build the fotosvideos collection without changing source files or Dock geometry."""
import argparse
import concurrent.futures
import json
from pathlib import Path
from PIL import Image, ImageDraw
import prepare_twigal_batch as batch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    batch.RELEASE = "https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v6"
    files = sorted(p for p in args.source.iterdir() if p.is_file() and not p.name.startswith("."))
    jobs = []
    counts = {"static": 0, "live": 0, "video": 83}
    for source in files:
        suffix = source.suffix.lower()
        assert suffix in (".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov"), source
        if suffix in (".mp4", ".mov"):
            kind = "video"
        else:
            with Image.open(source) as im:
                kind = "live" if getattr(im, "n_frames", 1) > 1 else "static"
        counts[kind] += 1
        number = counts[kind]
        asset_id = f"twigal-mp4-{number:02d}" if kind == "video" else f"studio-{kind}-{number:02d}"
        title = f"TwiGal {number:02d}" if kind == "video" else f"{kind.title()} {number:02d}"
        jobs.append((source, asset_id, title))
    def prepare(job):
        source, asset_id, title = job
        anchors = {"studio-live-02": 0.10, "studio-live-05": 0.65,
                   "studio-live-16": 0.10, "studio-live-24": 0.72,
                   "studio-static-32": 0.28, "studio-static-34": 0.85,
                   "studio-static-35": 0.90, "studio-static-36": 0.25}
        return batch.prepare(source, args.output, asset_id=asset_id, asset_title=title,
                             crop_anchor=anchors.get(asset_id))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(prepare, jobs))
    old = json.loads((batch.REPO / "catalogs/dock-v1.json").read_text())
    catalog = dict(old, themes=old["themes"] + [r["theme"] for r in results])
    ids = [t["id"] for t in catalog["themes"]]
    assert len(ids) == len(set(ids))
    encoded = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    assert len(encoded.encode()) < 512 * 1024
    (args.output / "catalog.json").write_text(encoded)
    (args.output / "manifest.json").write_text(json.dumps(results, indent=2) + "\n")
    for start in range(0, len(results), 24):
        chunk = results[start:start + 24]
        sheet = Image.new("RGB", (1200, ((len(chunk) + 2) // 3) * 145), "#202020")
        draw = ImageDraw.Draw(sheet)
        for i, record in enumerate(chunk):
            x, y = i % 3 * 400, i // 3 * 145
            with Image.open(args.output / "previews" / (record["theme"]["id"] + ".png")) as im:
                sheet.paste(im.resize((382, 106)), (x + 8, y + 2))
            draw.text((x + 8, y + 113), record["theme"]["title"], fill="white")
        sheet.save(args.output / f"contact-{start // 24 + 1}.jpg")
    print(json.dumps({"total": len(ids), "added": len(results), "static": counts["static"],
                      "live": counts["live"] + counts["video"] - 83}), flush=True)


if __name__ == "__main__":
    main()

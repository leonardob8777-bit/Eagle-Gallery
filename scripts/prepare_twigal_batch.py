#!/usr/bin/env python3
"""Prepare the September TwiGal batch; never modify source files or app geometry."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat

WIDTH, HEIGHT, FPS, COUNT = 1146, 318, 6, 17
REPO = Path(__file__).resolve().parents[1]
REMOTE = "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews"
RELEASE = "https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v3"


def run(args):
    result = subprocess.run(args, capture_output=True, check=True)
    return result.stdout


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(source, output, theme_number=None):
    animated = source.suffix.lower() in (".mp4", ".mov")
    number = re.search(r"\d+", source.stem)
    number = int(number.group()) if number else 1
    if theme_number is not None:
        number = theme_number
    ext = source.suffix.lower()[1:]
    theme_id = f"twigal-{ext}-{number:02d}" if animated else "twigalaxy"
    title = f"TwiGal {number:02d}" + (" · MOV" if ext == "mov" else "") if animated else "TwiGalaxy"
    frame_dir = output / "frames" / theme_id
    frame_dir.mkdir(parents=True, exist_ok=False)
    source_hash = digest(source)
    probe = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate:format=duration", "-of", "json", str(source)]))
    count = COUNT if animated else 1
    # Aspect-fill from the uncropped original. No baked capsule, padding, tint,
    # or transparent corners: the unchanged native Dock supplies its exact mask.
    filter_complex = None
    if theme_number is not None and 76 <= theme_number <= 83:
        # Subject-aware vertical crops for the next eight imports: keep the
        # cloud, moon, faces and car wheels visible at the established scale.
        anchor = {76: 0.025, 77: 0.36, 78: 0.40, 79: 0.12,
                  80: 0.50, 81: 0.50, 82: 0.72, 83: 0.30}[theme_number]
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1146:318:0:(ih-oh)*{anchor},setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-01":
        # Keep the standard aspect-fill appearance but look 140 output pixels
        # above center so the flying character remains inside the Dock crop.
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2-140,setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-02":
        # Lower the source crop so the seated pool character and both arms are
        # visible, while retaining the standard full-bleed Dock treatment.
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2+180,setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-03":
        # Raise the artwork inside the Dock so the lower pointed end of the
        # vertical spiral remains visible instead of falling below the crop.
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2+620,setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-18":
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2+25,setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-21":
        # The center crop contained mostly empty sky. Lower the sampled region
        # to frame the hand and bouquet together.
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2+250,setsar=1,format=rgb24"
        )
    elif theme_id == "twigal-mp4-22":
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2-300,setsar=1,format=rgb24"
        )
    elif theme_id in ("twigal-mp4-23", "twigal-mp4-28"):
        # These 0.24-second square clips lose their subject under a 3.6:1
        # aspect-fill. Keep the entire subject and extend the same moving frame
        # behind it so the Dock remains full bleed without a hard color fill.
        filters = None
        filter_complex = (
            "[0:v]fps=6,split=2[bg][fg];"
            "[bg]scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318,gblur=sigma=24[back];"
            "[fg]scale=-2:318:flags=lanczos[front];"
            "[back][front]overlay=(W-w)/2:0,setsar=1,format=rgb24[out]"
        )
    elif theme_id == "twigal-mp4-40":
        filters = (
            "fps=6,scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318:0:(ih-oh)/2-260,setsar=1,format=rgb24"
        )
    else:
        filters = ("fps=6," if animated else "") + (
            "scale=1146:318:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1146:318,setsar=1,format=rgb24")
    command = ["ffmpeg", "-nostdin", "-v", "error", "-xerror"]
    if animated:
        command += ["-stream_loop", "-1"]
    command += ["-i", str(source), "-an"]
    if filter_complex:
        command += ["-filter_complex", filter_complex, "-map", "[out]"]
    else:
        command += ["-vf", filters]
    command += ["-frames:v", str(count), "-threads", "1", str(frame_dir / "frame%02d.png")]
    run(command)
    frames = sorted(frame_dir.glob("frame*.png"))
    assert len(frames) == count, (source, len(frames))
    for frame in frames:
        with Image.open(frame) as im:
            im.load()
            assert im.size == (WIDTH, HEIGHT) and im.mode == "RGB", frame
    previews = output / "previews"
    previews.mkdir(exist_ok=True)
    preview = previews / f"{theme_id}.png"
    shutil.copyfile(frames[0], preview)
    with Image.open(preview) as im:
        rgb = tuple(round(v) for v in ImageStat.Stat(im.resize((1, 1))).mean[:3])
    accent = "#" + "".join(f"{v:02X}" for v in rgb)
    if animated:
        run(["ffmpeg", "-nostdin", "-v", "error", "-framerate", str(FPS),
            "-i", str(frame_dir / "frame%02d.png"), "-filter_complex",
            "scale=573:159:flags=lanczos,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a",
            "-threads", "1", "-loop", "0", str(previews / f"{theme_id}.gif")])
        with Image.open(previews / f"{theme_id}.gif") as gif:
            assert gif.n_frames == COUNT and gif.size == (573, 159)
            durations = []
            for i in range(gif.n_frames):
                gif.seek(i)
                durations.append(gif.info["duration"])
            assert abs(sum(durations) - COUNT / FPS * 1000) < 25
    package = output / "packages" / f"{theme_id}.zip"
    package.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for frame in frames:
            info = zipfile.ZipInfo(frame.name, date_time=(2026, 9, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, frame.read_bytes())
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == [f"frame{i:02d}.png" for i in range(1, count + 1)]
    assert 0 < package.stat().st_size <= 30 * 1024 * 1024
    assert digest(source) == source_hash, "Source changed during preparation"
    theme = dict(id=theme_id, version=1, title=title, titleES=title,
        subtitle="", subtitleES="", accent=accent, previewURL=f"{REMOTE}/{theme_id}.png",
        packageURL=f"{RELEASE}/{theme_id}.zip", sha256=digest(package),
        byteCount=package.stat().st_size, frameCount=count, fps=FPS if animated else 1,
        width=WIDTH, height=HEIGHT)
    if animated:
        theme["animatedPreviewURL"] = f"{REMOTE}/{theme_id}.gif"
    print(f"READY {theme_id}: {count} frames, {package.stat().st_size:,} bytes", flush=True)
    return dict(theme=theme, source=str(source), sourceSHA256=source_hash, probe=probe,
        crop="center aspect-fill; unchanged native mask", shortClips="repeat at source speed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    files = sorted(p for p in args.source.iterdir() if p.suffix.lower() in (".mp4", ".mov", ".png"))
    assert len(files) == 69
    assert sum(p.suffix.lower() in (".mp4", ".mov") for p in files) == 68
    args.output.mkdir(parents=True, exist_ok=False)
    old = json.loads((REPO / "catalogs/dock-v1.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda source: prepare(source, args.output), files))
    results.sort(key=lambda r: r["theme"]["id"])
    new = [r["theme"] for r in results]
    ids = [t["id"] for t in old["themes"] + new]
    assert len(set(ids)) == len(ids)
    catalog = dict(old, themes=old["themes"] + new)
    encoded = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    assert len(encoded.encode()) < 512 * 1024
    (args.output / "catalog.json").write_text(encoded)
    (args.output / "manifest.json").write_text(json.dumps(results, indent=2) + "\n")
    # A contact sheet for checking the prepared media, not a new gallery asset.
    for start in range(0, len(results), 24):
        chunk = results[start:start + 24]
        sheet = Image.new("RGB", (1200, ((len(chunk) + 2) // 3) * 135), "#202020")
        draw = ImageDraw.Draw(sheet)
        for i, record in enumerate(chunk):
            x, y = (i % 3) * 400, (i // 3) * 135
            with Image.open(args.output / "previews" / (record["theme"]["id"] + ".png")) as im:
                sheet.paste(im.resize((382, 106)), (x + 8, y + 2))
            draw.text((x + 8, y + 111), record["theme"]["id"], fill="white")
        sheet.save(args.output / f"contact-{start // 24 + 1}.jpg")
    print(json.dumps(dict(themes=len(catalog["themes"]), added=len(new),
        packageBytes=sum(t["byteCount"] for t in new), originalFilesUnchanged=True)), flush=True)


if __name__ == "__main__":
    main()

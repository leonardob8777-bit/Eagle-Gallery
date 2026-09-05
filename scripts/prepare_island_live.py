#!/usr/bin/env python3
"""Sample a video into Vortex's exact existing alpha canvas, without editing it."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("vortex", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
source_hash, template_hash = sha(args.source), sha(args.vortex)
args.output.mkdir(parents=True, exist_ok=False)
raw = args.output / "raw"
frames = args.output / "frames"
raw.mkdir()
frames.mkdir()
with Image.open(args.vortex) as reference:
    assert reference.mode == "RGBA" and reference.size == (1200, 500)
    alpha = reference.getchannel("A").copy()
left, top, right, bottom = alpha.getbbox()
width, height = right-left, bottom-top
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-stream_loop", "-1",
                "-i", str(args.source), "-an", "-vf",
                f"fps=6,scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={width}:{height}:(iw-ow)/2:(ih-oh)*0.22,setsar=1,format=rgb24",
                "-frames:v", "17", "-threads", "1", str(raw / "frame%02d.png")], check=True)
hashes = []
for index in range(1, 18):
    canvas = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
    with Image.open(raw / f"frame{index:02d}.png") as frame:
        canvas.paste(frame, (left, top))
    canvas.putalpha(alpha)
    # Keep zero-alpha RGB empty too, avoiding hidden rectangular colour data
    # in thumbnail decoders that do not composite transparency correctly.
    canvas.paste((0, 0, 0, 0), mask=alpha.point(lambda value: 255 if value == 0 else 0))
    path = frames / f"frame{index:02d}.png"
    canvas.save(path, optimize=True)
    assert path.stat().st_size <= 448 * 1024
    with Image.open(path) as checked:
        assert checked.getchannel("A").tobytes() == alpha.tobytes()
    hashes.append(sha(path))
package = args.output / "singularity-live-v1.zip"
with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(frames.glob("*.png")):
        archive.write(path, path.name)
with zipfile.ZipFile(package) as archive:
    assert archive.testzip() is None and len(archive.namelist()) == 17
assert package.stat().st_size <= 8 * 1024 * 1024
previews = args.output / "previews"
previews.mkdir()
(previews / "singularity-live.png").write_bytes((frames / "frame01.png").read_bytes())
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-framerate", "6", "-i",
                str(frames / "frame%02d.png"), "-filter_complex",
                "scale=600:250:flags=lanczos,split[a][b];[a]palettegen=reserve_transparent=1[p];"
                "[b][p]paletteuse=dither=sierra2_4a:alpha_threshold=128", "-loop", "0",
                str(previews / "singularity-live.gif")], check=True)
manifest = dict(schemaVersion=1, id="singularity-live", version=1,
                packageURL="https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/island-v1/singularity-live-v1.zip",
                sha256=sha(package), byteCount=package.stat().st_size,
                frameCount=17, fps=6, width=1200, height=500, frameSHA256=hashes)
(args.output / "island-live-v1.json").write_text(json.dumps(manifest, indent=2) + "\n")
assert sha(args.source) == source_hash and sha(args.vortex) == template_hash
(args.output / "verification.json").write_text(json.dumps(dict(source=str(args.source), sourceSHA256=source_hash,
    vortexSHA256=template_hash, alphaMatchesVortex=True, alphaBounds=list(alpha.getbbox()),
    frames=17, fps=6, canvas=[1200, 500], sourceUnchanged=True), indent=2) + "\n")
print(json.dumps(manifest), flush=True)

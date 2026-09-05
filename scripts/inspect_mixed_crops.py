"""Create a source contact sheet for crop inspection; never alter originals."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

output = Path(sys.argv[1])
records = json.loads((output / "manifest.json").read_text())
ids = {"studio-live-02", "studio-live-05", "studio-live-16", "studio-live-24",
       "studio-static-32", "studio-static-34", "studio-static-35", "studio-static-36"}
sheet = Image.new("RGB", (1200, 640), "#202020")
draw = ImageDraw.Draw(sheet)
for i, record in enumerate(r for r in records if r["theme"]["id"] in ids):
    x, y = i % 4 * 300, i // 4 * 320
    with Image.open(record["source"]) as source:
        thumb = ImageOps.contain(source.convert("RGB"), (290, 290))
        sheet.paste(thumb, (x + (300 - thumb.width) // 2, y))
    draw.text((x + 5, y + 298), record["theme"]["id"], fill="white")
sheet.save(output / "crop-sources.jpg")

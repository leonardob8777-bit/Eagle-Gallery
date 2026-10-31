#!/usr/bin/env python3
"""Build installable static digit packages from Eagle's nine HTML key designs.

The source ZIP contains animated full-screen HTML, not TelephonyUI images. This
script reproduces each design's key shape and palette as ten transparent PNGs.
It does not turn the full-screen animation into a system Passcode animation.
"""

import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "passcode" / "packages"
PREVIEW_DIR = ROOT / "previews" / "passcode" / "applicable"
CATALOG = ROOT / "catalogs" / "passcode-v1.json"
S = 3
SIDE = 256
P = SIDE * S
FONT_REGULAR = "/System/Library/Fonts/SFCompact.ttf"
FONT_MONO = "/System/Library/Fonts/SFNSMono.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_ROUNDED = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"


def rgba(hex_value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def box(n: int) -> int:
    return n * S


def make_digit(theme: str, digit: str) -> bytes:
    image = Image.new("RGBA", (P, P))
    draw = ImageDraw.Draw(image)
    center = P // 2
    inset = box(25)
    outer = (inset, inset, P - inset, P - inset)
    font_file = FONT_REGULAR
    font_size = 112
    fill = rgba("ffffff")

    if theme == "orbit":
        draw.ellipse(outer, fill=rgba("141230", 235), outline=rgba("8b7bff"), width=box(3))
        draw.ellipse((box(37), box(37), P - box(37), P - box(37)), outline=rgba("4a4d86"), width=box(2))
        fill = rgba("eef0ff")
    elif theme == "terminal":
        draw.rounded_rectangle(outer, radius=box(4), fill=rgba("040706", 235), outline=rgba("2a6b46"), width=box(3))
        draw.line((box(43), box(60), box(43), box(194)), fill=rgba("4dff9a", 120), width=box(2))
        font_file, font_size, fill = FONT_MONO, 101, rgba("4dff9a")
    elif theme == "liquid-glass":
        draw.rounded_rectangle(outer, radius=box(68), fill=rgba("c9d8f3", 104), outline=rgba("ffffff", 230), width=box(3))
        draw.arc((box(36), box(35), P - box(36), P - box(35)), 190, 340, fill=rgba("ffffff", 220), width=box(4))
        fill = rgba("ffffff")
    elif theme == "brutal-paper":
        draw.rectangle((box(35), box(35), P - box(13), P - box(13)), fill=rgba("111111"))
        draw.rectangle((box(21), box(21), P - box(29), P - box(29)), fill=rgba("ffffff"), outline=rgba("111111"), width=box(6))
        font_file, font_size, fill = FONT_BOLD, 104, rgba("111111")
    elif theme == "synthwave":
        glow = Image.new("RGBA", (P, P))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle(outer, radius=box(35), outline=rgba("ff4fd8", 180), width=box(9))
        image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(box(10))))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(outer, radius=box(35), fill=rgba("12002b", 235), outline=rgba("ff4fd8"), width=box(4))
        draw.rounded_rectangle((box(35), box(35), P - box(35), P - box(35)), radius=box(27), outline=rgba("00fff0", 140), width=box(2))
        font_file, font_size, fill = FONT_MONO, 103, rgba("ffffff")
    elif theme == "pumpkin-night":
        draw.ellipse((box(27), box(35), P - box(27), P - box(24)), fill=rgba("d55b14"))
        draw.ellipse((box(34), box(31), P - box(34), P - box(32)), fill=rgba("f2761b"), outline=rgba("ffb04a"), width=box(4))
        draw.arc((box(47), box(40), P - box(47), P - box(57)), 200, 338, fill=rgba("ffd071", 180), width=box(5))
        font_file, font_size, fill = FONT_ROUNDED, 108, rgba("2a1206")
    elif theme == "aurora":
        points = [(center, box(17)), (box(224), box(68)), (box(224), box(188)), (center, box(239)), (box(32), box(188)), (box(32), box(68))]
        draw.polygon(points, fill=rgba("c9fff0", 75))
        draw.line(points + [points[0]], fill=rgba("b9ffe8"), width=box(3), joint="curve")
        font_file, font_size, fill = FONT_REGULAR, 111, rgba("eafff8")
    elif theme == "abyss":
        draw.ellipse(outer, fill=rgba("04263b", 155), outline=rgba("e4fbff", 180), width=box(3))
        draw.ellipse((box(37), box(31), box(110), box(76)), fill=rgba("ffffff", 70))
        draw.arc((box(36), box(35), P - box(36), P - box(35)), 20, 150, fill=rgba("7fe7ff", 145), width=box(5))
        font_file, font_size, fill = FONT_REGULAR, 110, rgba("e4fbff")
    elif theme == "blueprint":
        draw.rectangle(outer, fill=rgba("163762", 140), outline=rgba("ffffff"), width=box(4))
        for x in (58, 198):
            draw.line((box(x), box(38), box(x), box(218)), fill=rgba("ffffff", 45), width=box(2))
        for y in (58, 198):
            draw.line((box(38), box(y), box(218), box(y)), fill=rgba("ffffff", 45), width=box(2))
        font_file, font_size, fill = FONT_MONO, 104, rgba("ffffff")
    else:
        raise ValueError(theme)

    font = ImageFont.truetype(font_file, box(font_size))
    bounds = draw.textbbox((0, 0), digit, font=font)
    x = center - (bounds[2] - bounds[0]) / 2 - bounds[0]
    y = center - (bounds[3] - bounds[1]) / 2 - bounds[1]
    draw.text((x, y), digit, font=font, fill=fill)
    image = image.resize((SIDE, SIDE), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def main() -> None:
    catalog = json.loads(CATALOG.read_text())
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    assert len(catalog["themes"]) == 9
    for theme in catalog["themes"]:
        identifier = theme["id"]
        destination = PACKAGE_DIR / f"{identifier}-v1.passthm"
        digits = {digit: make_digit(identifier, digit) for digit in "0123456789"}
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for digit in "0123456789":
                info = zipfile.ZipInfo(f"{digit}.png", date_time=(2026, 10, 31, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, digits[digit], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        preview = Image.new("RGB", (780, 1387), "#11141e")
        preview_draw = ImageDraw.Draw(preview)
        title_font = ImageFont.truetype(FONT_BOLD, 58)
        caption_font = ImageFont.truetype(FONT_REGULAR, 30)
        preview_draw.text((76, 88), theme["name"], fill="#ffffff", font=title_font)
        preview_draw.text((76, 170), "NÚMEROS DEL CÓDIGO", fill="#b0b7c8", font=caption_font)
        for index, digit in enumerate("123456789"):
            image = Image.open(io.BytesIO(digits[digit])).convert("RGBA").resize((190, 190), Image.Resampling.LANCZOS)
            preview.paste(image, (75 + (index % 3) * 218, 280 + (index // 3) * 234), image)
        zero = Image.open(io.BytesIO(digits["0"])).convert("RGBA").resize((190, 190), Image.Resampling.LANCZOS)
        preview.paste(zero, (293, 1010), zero)
        preview_draw.text((76, 1290), "DISEÑO APLICABLE", fill="#b0b7c8", font=caption_font)
        preview.save(PREVIEW_DIR / f"{identifier}.png", optimize=True)
        theme["preview"] = (
            "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/"
            f"previews/passcode/applicable/{identifier}.png"
        )
        theme["description"] = "Números aplicables. Fondo a juego en Fondos; animación solo en la vista previa."
        theme["wallpaperID"] = identifier
        theme["url"] = (
            "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/"
            f"passcode/packages/{destination.name}"
        )
        theme["byteCount"] = destination.stat().st_size
        theme["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        print(identifier, destination.stat().st_size, theme["sha256"])
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

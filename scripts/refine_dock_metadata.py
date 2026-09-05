"""Apply reviewed names and representative artwork colors, preserving media and IDs."""
import colorsys
import json
from collections import defaultdict
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def artwork_accent(path):
    samples = []
    with Image.open(path) as image:
        count = getattr(image, 'n_frames', 1)
        for frame in sorted({round(i * (count - 1) / 4) for i in range(5)}):
            image.seek(frame)
            sample = image.convert('RGBA')
            sample.thumbnail((96, 32))
            samples.extend(pixel[:3] for pixel in sample.getdata() if pixel[3] > 220)
    groups = defaultdict(list)
    for r, g, b in samples:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s >= 0.22 and v >= 0.16:
            groups[int(h * 24) % 24].append((r, g, b, s * v))
    if not groups or sum(map(len, groups.values())) < len(samples) * 0.015:
        # Neutral artwork remains neutral, with contrast on both light/dark UI.
        return '#A8A8A8'
    hue = max(groups, key=lambda k: sum(p[3] for p in groups[k]))
    cluster = groups[hue] + groups[(hue - 1) % 24] + groups[(hue + 1) % 24]
    weight = sum(p[3] for p in cluster)
    rgb = [sum(p[channel] * p[3] for p in cluster) / weight / 255 for channel in range(3)]
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    rgb = colorsys.hsv_to_rgb(h, s, max(v, 0.72))
    return '#' + ''.join(f'{round(c * 255):02X}' for c in rgb)


def main():
    path = ROOT / 'catalogs/dock-v1.json'
    catalog = json.loads(path.read_text())
    names = json.loads((ROOT / 'metadata/dock-theme-names.json').read_text())
    assert set(names).issubset({t['id'] for t in catalog['themes']})
    for theme in catalog['themes']:
        if theme['id'] in names:
            theme['title'] = names[theme['id']]
            theme['titleES'] = names[theme['id']]
        extension = '.gif' if theme.get('animatedPreviewURL') else '.png'
        theme['accent'] = artwork_accent(ROOT / 'previews' / (theme['id'] + extension))
    assert len({t['title'].casefold() for t in catalog['themes']}) == len(catalog['themes'])
    encoded = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
    assert len(encoded.encode()) < 512 * 1024
    path.write_text(encoded)
    print(f"Updated {len(names)} names and {len(catalog['themes'])} artwork colors")


if __name__ == '__main__':
    main()

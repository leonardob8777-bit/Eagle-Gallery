#!/usr/bin/env python3
"""User-selected October Dock media. Prepare locally; publication is separate."""
import concurrent.futures
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import prepare_twigal_batch as batch

OUT = batch.REPO.parent / 'Eagle-Gallery-Builds/2026-10-15-dock-reviewed'
SOURCE = Path('/Users/leonardobaptiste/Downloads')
RECORDS = [
 ('IMG_3198.JPG', 'Minion Trio', 'Trío amarillo', .0),
 ('IMG_3196.JPG', 'Deep Thought', 'Pensamiento profundo', .5),
 ('IMG_3185.JPG', 'Orange Revenge', 'Revancha naranja', .3),
 ('IMG_3186.JPG', 'Desert Shades', 'Gafas del desierto', .35),
 ('IMG_3187.JPG', 'Vice Crew', 'Banda de Vice', .35),
 ('IMG_3188.JPG', 'Pink Anthem', 'Himno rosa', .0),
 ('IMG_3189.JPG', 'Spider Peek', 'Mirada arácnida', .5),
 ('IMG_3190.JPG', 'Tiger Swag', 'Estilo tigre', .5),
 ('IMG_3191.JPG', 'Leopard Union', 'Unión leopardo', .5),
 ('IMG_3192.JPG', 'Crimson Pagoda', 'Pagoda carmesí', .48),
 ('IMG_3193.JPG', 'Flying Pigs', 'Cerdos voladores', .35),
 ('IMG_3194.JPG', 'San Andreas Ride', 'Paseo San Andreas', .0),
 ('IMG_3195.JPG', 'Block Sunset Cat', 'Gato al atardecer', .9),
 ('IMG_3197.JPG', 'Rabbid Crowd', 'Multitud de conejos', .5),
 ('IMG_3183.JPG', 'Street Collage', 'Collage urbano', .5),
 ('IMG_3184.JPG', 'Be Yourself', 'Sé tú mismo', .5),
 ('IMG_3180.JPG', 'Tiger Celebration', 'Celebración del tigre', .5),
 ('IMG_3182.JPG', 'Trust the Process', 'Confía en el proceso', .5),
 ('D2AD5137-3AE0-48E1-B2BD-B0D16B87B3FB.GIF', 'Pastel Nyan', 'Nyan pastel', .5),
 ('95D56441-E7CC-427A-A926-26DC0A2D5600.GIF', 'Mint Orbit', 'Órbita menta', .5),
 ('2A057F8E-6444-4A98-9F3C-481DEAC024B8.GIF', 'Pixel Getaway', 'Escape píxel', .38),
 ('FF402EB8-124E-485C-B4DA-8EF17A0EFAB5.GIF', 'Cosmic Passenger', 'Pasajero cósmico', .4),
 ('5E1C30F2-8F9C-4513-AFC4-F9E4085A7CB1.GIF', 'Neon Whale', 'Ballena neón', .5),
 ('3B457E1A-1F85-4531-A181-D8D021E30109.GIF', 'Tentacle Twist', 'Giro de tentáculo', .6),
 ('95E6A7A7-7B79-41FF-A977-AEC8B2F0C006.GIF', 'Pixel Abduction', 'Abducción píxel', .48),
 ('3AE266D3-811B-4763-A0BA-2DC2C4A518B4.GIF', 'Matter Pop', 'Materia pop', .5),
 ('D351B7F7-F370-4A25-B9AC-19EC43BB0E49.GIF', 'Star Parade', 'Desfile de estrellas', .5),
 ('32347FD5-64BB-4AAD-8968-302248725077.GIF', 'Electric Celebration', 'Celebración eléctrica', .4),
 ('61997F7C-0BD1-43A4-AD71-036D4B489DEA.GIF', 'Rainbow Driver', 'Conductor arcoíris', .45),
 ('456A90C8-5B37-44AC-B114-C3ABBE8427D8.GIF', 'Spider Stickers', 'Pegatinas arácnidas', .5),
 ('18EF3C0C-CBDB-43CB-A27F-6A5C18508F95.GIF', 'Pixel Earth', 'Tierra píxel', .5),
]

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    before = json.loads((batch.REPO / 'catalogs/dock-v1.json').read_text())
    write(OUT / 'before.json', before)
    batch.RELEASE = 'https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v9'
    def build(job):
        index, (filename, title, spanish, anchor) = job
        result = batch.prepare(SOURCE / filename, OUT, asset_id=f'october-dock-{index:02d}',
                               asset_title=title, crop_anchor=anchor)
        result['theme']['titleES'] = spanish
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        entries = list(pool.map(build, enumerate(RECORDS, 1)))
    write(OUT / 'manifest.json', entries)
    write(OUT / 'catalog.json', dict(before, themes=before['themes'] + [e['theme'] for e in entries]))
    sheet = Image.new('RGB', (1200, 11 * 140), '#202020')
    draw = ImageDraw.Draw(sheet)
    for i, entry in enumerate(entries):
        t = entry['theme']
        with Image.open(OUT / 'previews' / (t['id'] + '.png')) as im:
            sheet.paste(im.resize((382, 106)), (i % 3 * 400 + 8, i // 3 * 140))
        draw.text((i % 3 * 400 + 8, i // 3 * 140 + 110), t['title'], fill='white')
    sheet.save(OUT / 'contact.jpg')
    verify()

def verify():
    before = json.loads((OUT / 'before.json').read_text())
    catalog = json.loads((OUT / 'catalog.json').read_text())
    entries = json.loads((OUT / 'manifest.json').read_text())
    assert catalog['themes'][:len(before['themes'])] == before['themes']
    assert len(set(t['id'] for t in catalog['themes'])) == len(catalog['themes'])
    assert (OUT / 'catalog.json').stat().st_size <= 512 * 1024
    assert len(entries) == 31
    frames = 0
    for entry in entries:
        t = entry['theme']
        assert batch.digest(Path(entry['source'])) == entry['sourceSHA256']
        package = OUT / 'packages' / (t['id'] + '.zip')
        assert batch.digest(package) == t['sha256']
        assert package.stat().st_size == t['byteCount'] <= 30 * 1024 * 1024
        assert (t['frameCount'], t['fps']) in [(1, 1), (17, 6)]
        hashes = set()
        with zipfile.ZipFile(package) as z:
            assert z.testzip() is None
            assert z.namelist() == [f'frame{i:02d}.png' for i in range(1, t['frameCount'] + 1)]
            for name in z.namelist():
                with Image.open(io.BytesIO(z.read(name))) as im:
                    im.load()
                    assert im.size == (1146, 318) and im.mode == 'RGB'
                    hashes.add(hashlib.sha256(im.tobytes()).hexdigest())
                frames += 1
        assert (len(hashes) > 1) == (t['frameCount'] > 1), t['id']
    report = dict(added=31, static=18, live=13, total=len(catalog['themes']),
                  framesVerified=frames, originalsUnchanged=True, existingEntriesUnchanged=True)
    write(OUT / 'verified.json', report)
    print(json.dumps(report), flush=True)

if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify}[sys.argv[1]]()

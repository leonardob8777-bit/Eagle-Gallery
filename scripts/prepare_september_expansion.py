#!/usr/bin/env python3
"""Stage the September server-only media expansion; never publish automatically."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import prepare_twigal_batch as dock
from refine_dock_metadata import artwork_accent

ROOT = Path(__file__).resolve().parents[1]
BUILDS = ROOT.parent / 'Eagle-Gallery-Builds'
OUT = BUILDS / '2026-09-08-server-expansion'
SOURCE = Path.home() / 'Downloads/New Folder With Items'
VORTEX = ROOT.parent / 'Eagle-Beta11/lara/other/media.xcassets/PhotoAuraVortex.imageset/PhotoAuraVortex.png'
NAMES = ['Violet Hyperdrive', 'Runway Reflections', 'Soft Focus', 'Pixel Brothers',
    'Crimson Eye', 'Cloud Warp', 'Yeah Pop', 'Cosmic Spiral', 'Night Flight',
    'Violet Helix', 'Prism Horizon', 'Victory Night', 'Ink Surge', 'Event Horizon',
    'Magenta Vortex', 'Rainbow Shore', 'Comic Yawn', 'Pixel Blossom', 'Astro Type',
    'Loading Dots', 'Liquid Chrome', 'Chromatic Fracture', 'Pink Wormhole',
    'Heart Passage', 'Ghost Signal', 'Violet Skies', 'Monochrome Melt', 'Ink Cloud',
    'Plastic Pop', 'Neon Capsule', 'Scarlet Gaze', 'Phantom Eyes', 'Rose Galaxy',
    'Stellar Eclipse', 'Signal Ghosts', 'Spectrum Wave', 'Ink Motion', 'Blue Coil',
    'Purple Velocity', 'Brush Dance', 'Rebel Star', 'Neon Smile', 'Crimson Hearts',
    'Petal Hearts', 'Sunset Drive', 'Solar Kick', 'World Is Yours', 'Heavenly Light',
    'Cloud Angels', 'Celestial Storm', 'Leopard Gold', 'Camo Stars', 'Masked Blue',
    'Blue Eleven', 'Scarlet Stripes', 'Golden Victory', 'Trophy Glow', 'Victory Portrait',
    'Sunflower Nineteen', 'Golden Fields', 'Brazil Spirit', 'Number Ten']
# Indices refer to the saved, reviewed contact sheets (all 428 existing themes).
# Large shapes, all-over patterns, flowing light and readable edge colour survive
# the physical Island covering the middle. Portraits and long text do not.
OLD_SELECTION = [4,7,9,13,16,17,18,20,21,23,25,26,30,32,36,37,38,39,41,43,
    45,46,49,53,57,58,59,60,61,62,64,65,67,69,70,71,74,75,77,78,80,81,82,
    84,86,87,89,90,92,99,101,102,103,104,105,106,107,110,112,113,114,
    117,118,119,120,121,127,128,131,132,133,134,141,142,143,145,146,
    152,153,154,156,157,158,160,163,164,167,168,169,171,174,175,176,178,
    180,181,184,192,194,195,198,200,205,206,214,215,216,217,218,219,229,
    232,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,
    268,269,270,271,277,278,279,280,299,300,303,318,319,320,321,322,
    323,324,325,326,327,328,329,330,331,332,333,337,341,342,343,344,
    352,354,355,358,359,362,363,365,366,372,373,378,387,390,
    400,407,409,418,419,421,424,425]
NEW_SELECTION = [1,6,8,10,11,13,14,15,16,18,21,22,23,24,26,27,28,
    30,33,34,35,36,37,38,39,40,43,44,49,50,51,52]
REJECTED_AFTER_MASK_REVIEW = {
    'twigal-mov-04': 'Stars become too faint at small Island size',
    'studio-live-03': 'Animation includes tiny central text that loses legibility',
    'studio-live-14': 'Thin central heartbeat leaves the visible perimeter mostly empty',
    'studio-live-19': 'Thin central heartbeat leaves the visible perimeter mostly empty',
}
ISLAND_TITLES = {
    'studio-live-22':'Scarlet Heart Tunnel',
    'studio-static-13':'Red Spiral',
    'september-live-014':'Horizon Flow',
    'september-live-022':'Neon Fracture',
}

def configured_records():
    records = json.loads((OUT / 'inventory.json').read_text())
    for record, name in zip(records, NAMES, strict=True):
        record['title'] = name
        record['cropAnchor'] = 0.25 if record['index'] in [12,25,31,32,42,53,54,55,56,57,58,60,61] else 0.5
    return records

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def inventory():
    OUT.mkdir(parents=True, exist_ok=False)
    existing = json.loads((ROOT / 'catalogs/dock-v1.json').read_text())
    existing_ids = {t['id'] for t in existing['themes']}
    hashes = {}
    for path in sorted(BUILDS.glob('*/manifest.json')):
        try:
            for record in json.loads(path.read_text()):
                if record['theme']['id'] in existing_ids:
                    hashes[record['sourceSHA256']] = record['theme']['id']
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
    files = sorted(p for p in SOURCE.iterdir() if p.is_file() and not p.name.startswith('.'))
    assert len(files) == 62
    counters = {'static': 0, 'live': 0}
    records = []
    for index, path in enumerate(files, 1):
        with Image.open(path) as im:
            kind = 'live' if getattr(im, 'n_frames', 1) > 1 else 'static'
            counters[kind] += 1
            source_hash = digest(path)
            records.append(dict(index=index, source=str(path), sourceSHA256=source_hash,
                kind=kind, dimensions=list(im.size), frames=getattr(im, 'n_frames', 1),
                existingID=hashes.get(source_hash), id=f'september-{kind}-{counters[kind]:03d}',
                title=f'September {kind.title()} {counters[kind]:02d}'))
    assert len({r['sourceSHA256'] for r in records}) == 62, 'Duplicate inputs need review'
    write_json(OUT / 'inventory.json', records)
    write_json(OUT / 'dock-before.json', existing)
    write_json(OUT / 'island-before.json', json.loads((ROOT / 'catalogs/island-gallery-v1.json').read_text()))
    contact_sources()
    print(json.dumps(dict(count=len(records), **counters, existing=sum(bool(r['existingID']) for r in records))))

def contact_sources():
    records = json.loads((OUT / 'inventory.json').read_text())
    for start in range(0, len(records), 24):
        chunk = records[start:start+24]
        sheet = Image.new('RGB', (1200, 800), '#202024')
        draw = ImageDraw.Draw(sheet)
        for offset, record in enumerate(chunk):
            x, y = offset % 6 * 200, offset // 6 * 200
            with Image.open(record['source']) as im:
                count = getattr(im, 'n_frames', 1)
                im.seek(min(count-1, count//3))
                thumb = ImageOps.contain(im.convert('RGB'), (192, 158))
                sheet.paste(thumb, (x+(200-thumb.width)//2, y))
            draw.text((x+5, y+160), f"{record['index']:02} {record['kind']} {record['dimensions']}", fill='white')
            draw.text((x+5, y+176), record['existingID'] or 'new', fill='#cccccc')
        sheet.save(OUT / f'sources-{start//24+1}.jpg')

def prepare_dock():
    records = configured_records()
    output = OUT / 'dock'
    output.mkdir(exist_ok=False)
    dock.RELEASE = 'https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v8'
    def prepare(record):
        if record['existingID']:
            return None
        result = dock.prepare(Path(record['source']), output, asset_id=record['id'],
                              asset_title=record['title'], crop_anchor=record.get('cropAnchor'))
        result['theme']['accent'] = artwork_accent(output / 'previews' / (record['id'] + '.png'))
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = [r for r in pool.map(prepare, records) if r is not None]
    old = json.loads((OUT / 'dock-before.json').read_text())
    catalog = dict(old, themes=old['themes']+[r['theme'] for r in results])
    assert len({t['id'] for t in catalog['themes']}) == len(catalog['themes'])
    write_json(output / 'catalog.json', catalog)
    write_json(output / 'manifest.json', results)
    assert (output / 'catalog.json').stat().st_size < 512*1024
    print(f"READY Dock: {len(results)} additions, {len(catalog['themes'])} total")

def candidates():
    catalog = json.loads((OUT / 'dock-before.json').read_text())
    themes = {t['id']:t for t in catalog['themes']}
    sources = {}
    for path in sorted(BUILDS.glob('*/manifest.json')):
        try:
            for record in json.loads(path.read_text()):
                if record['theme']['id'] in themes and Path(record['source']).is_file():
                    sources[record['theme']['id']] = record
        except (KeyError,TypeError,json.JSONDecodeError):
            continue
    records = []
    for theme in catalog['themes']:
        source = sources.get(theme['id'])
        if source:
            records.append(dict(id=theme['id'], title=theme['title'], source=source['source'],
                sourceSHA256=source['sourceSHA256'], kind='live' if theme['frameCount']==17 else 'static',
                preview=str(ROOT/'previews'/f"{theme['id']}.png")))
    for theme in catalog['themes']:
        if theme['id'] not in sources:
            records.append(dict(id=theme['id'], title=theme['title'], source=None,
                sourceSHA256=None, theme=theme, kind='live' if theme['frameCount']==17 else 'static',
                preview=str(ROOT/'previews'/f"{theme['id']}.png")))
    write_json(OUT/'candidates.json',records)
    for start in range(0,len(records),60):
        sheet=Image.new('RGB',(1400,900),'#16161a')
        draw=ImageDraw.Draw(sheet)
        for offset, record in enumerate(records[start:start+60]):
            x,y=offset%7*200,offset//7*100
            with Image.open(record['preview']) as im:
                thumb=ImageOps.contain(im.convert('RGB'),(194,63))
                sheet.paste(thumb,(x,y))
            draw.text((x+2,y+64),f"{start+offset+1:03} {record['kind']} {record['id']}",fill='white')
            draw.text((x+2,y+80),record['title'][:28],fill='#bbbbbb')
        sheet.save(OUT/f'candidates-{start//60+1}.jpg')
    print(f'{len(records)} existing candidates reviewed; {sum(r["source"] is None for r in records)} need source recovery')

def select_island():
    old = json.loads((OUT/'candidates.json').read_text())
    new = configured_records()
    chosen = [dict(old[i-1]) for i in OLD_SELECTION] + [dict(new[i-1]) for i in NEW_SELECTION]
    existing_hashes = set()
    for path in list((BUILDS/'2026-09-06-island-gifs').glob('*/verification.json')) + [BUILDS/'2026-09-05-island-live-final/verification.json']:
        existing_hashes.add(json.loads(path.read_text())['sourceSHA256'])
    selected, skipped = [], []
    seen = set(existing_hashes)
    for record in chosen:
        if record['id'] in REJECTED_AFTER_MASK_REVIEW:
            skipped.append(dict(id=record['id'],reason=REJECTED_AFTER_MASK_REVIEW[record['id']]))
            continue
        if not record['source'] and record['id'].startswith('twigal-mp4-'):
            original = SOURCE.parent/'videos'/f"TwiGal {int(record['id'].split('-')[-1])}.MP4"
            if original.is_file():
                record.update(source=str(original),sourceSHA256=digest(original))
        if record['sourceSHA256'] and record['sourceSHA256'] in seen:
            skipped.append(dict(id=record['id'],reason='Source already in Island or selected'))
            continue
        if record['sourceSHA256']:
            seen.add(record['sourceSHA256'])
        record['dockID'] = record['id']
        record['title'] = ISLAND_TITLES.get(record['dockID'],record['title'])
        record['id'] = 'island-' + record['id']
        record['cropAnchor'] = 0.5
        selected.append(record)
    write_json(OUT/'island-selection.json',selected)
    write_json(OUT/'island-skipped.json',skipped)
    print(json.dumps(dict(selected=len(selected),live=sum(r['kind']=='live' for r in selected),
        static=sum(r['kind']=='static' for r in selected),skipped=skipped,
        recover=[r['dockID'] for r in selected if not r['source']]),indent=2))

def recover_source(record):
    theme = record['theme']
    folder = OUT/'recovered'/record['dockID']
    folder.mkdir(parents=True,exist_ok=True)
    package = folder/(record['dockID']+'.zip')
    if not package.exists():
        release = theme['packageURL'].split('/')[-2]
        subprocess.run(['gh','release','download',release,'--repo','leonardob8777-bit/Eagle-Gallery',
            '--pattern',package.name,'--dir',str(folder)],check=True)
    assert digest(package)==theme['sha256'] and package.stat().st_size==theme['byteCount']
    with zipfile.ZipFile(package) as archive:
        names = [f'frame{i:02d}.png' for i in range(1,theme['frameCount']+1)]
        assert set(archive.namelist())==set(names)
        for name in names:
            (folder/name).write_bytes(archive.read(name))
    if record['kind']=='static':
        source = folder/'frame01.png'
    else:
        source = folder/'source.mkv'
        if not source.exists():
            subprocess.run(['ffmpeg','-nostdin','-v','error','-framerate','6','-i',str(folder/'frame%02d.png'),
                '-c:v','ffv1','-level','3',str(source)],check=True)
    record.update(source=str(source),sourceSHA256=digest(source),recoveredPackageSHA256=theme['sha256'])

def prepare_island():
    records = json.loads((OUT/'island-selection.json').read_text())
    output = OUT/'island'
    output.mkdir(exist_ok=True)
    def build(record):
        if not record['source']:
            recover_source(record)
        folder = output/record['id']
        if not (folder/'verification.json').exists():
            if folder.exists():
                folder.rename(output/f'.incomplete-{record["id"]}-{time.time_ns()}')
            result = subprocess.run([sys.executable,str(ROOT/'scripts/prepare_island_live.py'),
                record['source'],str(VORTEX),str(folder),'--id',record['id'],'--release','island-gifs-v1',
                '--crop-anchor',str(record['cropAnchor'])]+(['--still'] if record['kind']=='static' else []),capture_output=True,text=True)
            (output/(record['id']+'.log')).write_text(result.stdout+result.stderr)
            if result.returncode:
                raise RuntimeError(record['id']+': '+result.stderr[-1800:])
        theme = json.loads((folder/'island-live-v1.json').read_text())
        theme.update(title=record['title'],titleES=record['title'],
            accent=artwork_accent(folder/'previews'/f'{record["id"]}.gif'),
            previewURL=f'https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/{record["id"]}.gif',
            posterURL=f'https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/{record["id"]}.png')
        print(f"Ready Island: {record['title']} ({record['kind']})",flush=True)
        return dict(record=record,theme=theme)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(build,records))
    old = json.loads((OUT/'island-before.json').read_text())
    write_json(output/'manifest.json',results)
    write_json(output/'catalog.json',dict(old,themes=old['themes']+[r['theme'] for r in results]))
    print(f'READY Island: {len(results)} additions',flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['inventory', 'dock', 'contacts', 'candidates','select','island'])
    args = parser.parse_args()
    {'inventory': inventory, 'dock': prepare_dock, 'contacts': contact_sources, 'candidates': candidates,
        'select':select_island,'island':prepare_island}[args.command]()

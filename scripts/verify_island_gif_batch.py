"""Verify every new Island package against Singularity's exact alpha and timing."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent/'Eagle-Gallery-Builds/2026-09-06-island-gifs'
items = json.loads((ROOT/'metadata/island-gifs-v1.json').read_text())
themes = json.loads((ROOT/'catalogs/island-gallery-v1.json').read_text())['themes']
assert len(items) == 41 and len(themes) == 42
assert len({t['id'] for t in themes}) == len({t['title'] for t in themes}) == 42
assert themes[0]['id'] == 'singularity-live'
with Image.open(ROOT.parent/'Eagle-Beta11/lara/other/media.xcassets/PhotoAuraVortex.imageset/PhotoAuraVortex.png') as im:
    alpha = im.getchannel('A').tobytes()
sheet = Image.new('RGB',(1200,((len(items)+3)//4)*155),(22,22,24))
draw=ImageDraw.Draw(sheet)
total=0
for index,(item,theme) in enumerate(zip(items,themes[1:])):
    assert item['id']==theme['id']
    folder=OUT/theme['id']
    package=folder/f"{theme['id']}-v1.zip"
    assert package.stat().st_size==theme['byteCount']<=34*1024*1024
    assert hashlib.sha256(package.read_bytes()).hexdigest()==theme['sha256']
    assert (theme['frameCount'],theme['fps'],theme['width'],theme['height'])==(17,6,1200,500)
    verification=json.loads((folder/'verification.json').read_text())
    assert hashlib.sha256((Path('/Users/leonardobaptiste/Downloads')/item['source']).read_bytes()).hexdigest()==verification['sourceSHA256']
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())=={f'frame{i:02d}.png' for i in range(1,18)}
        for i in range(1,18):
            data=archive.read(f'frame{i:02d}.png')
            assert len(data)<=2*1024*1024
            assert hashlib.sha256(data).hexdigest()==theme['frameSHA256'][i-1]
            with Image.open(io.BytesIO(data)) as frame:
                assert frame.mode=='RGBA' and frame.size==(1200,500)
                assert frame.getchannel('A').tobytes()==alpha
        assert len(set(theme['frameSHA256']))>=2, f"No motion: {theme['id']}"
    with Image.open(ROOT/'previews/island'/f"{theme['id']}.gif") as preview:
        assert preview.size==(600,250) and preview.n_frames>1
        ms=0
        for i in range(preview.n_frames):
            preview.seek(i)
            ms+=preview.info['duration']
        assert abs(ms-17/6*1000)<25,(theme['id'],ms)
        preview.seek(preview.n_frames//2)
        image=preview.convert('RGBA')
        image.thumbnail((280,116))
        x,y=(index%4)*300+10,(index//4)*155
        sheet.paste(image,(x,y),image)
        draw.text((x,y+116),f"{index+1:02d}  {theme['title']}",fill='white')
    total+=theme['byteCount']
sheet.save(OUT/'contact-sheet.jpg')
print(f'PASS: 41 unchanged sources; 697 verified frames; exact Vortex alpha; moving previews at 6 FPS; {total} bytes online')
print(OUT/'contact-sheet.jpg')

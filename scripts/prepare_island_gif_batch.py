"""Build the reviewed GIF collection with the unchanged Singularity preset."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from refine_dock_metadata import artwork_accent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'Eagle-Gallery-Builds/2026-09-06-island-gifs'
DOWNLOADS = Path('/Users/leonardobaptiste/Downloads')
VORTEX = ROOT.parent / 'Eagle-Beta11/lara/other/media.xcassets/PhotoAuraVortex.imageset/PhotoAuraVortex.png'
items = json.loads((ROOT/'metadata/island-gifs-v1.json').read_text())
assert len(items) == 41 and len({i['id'] for i in items}) == 41
for item in items:
    assert (DOWNLOADS/item['source']).is_file(), item['source']
OUT.mkdir(parents=True, exist_ok=True)


def build(item):
    folder = OUT / item['id']
    verification = folder/'verification.json'
    if not verification.exists():
        if folder.exists():
            folder.rename(OUT/f".incomplete-{item['id']}-{time.time_ns()}")
        result = subprocess.run([sys.executable,str(ROOT/'scripts/prepare_island_live.py'),
            str(DOWNLOADS/item['source']),str(VORTEX),str(folder),
            '--id',item['id'],'--release','island-gifs-v1'],capture_output=True,text=True)
        (OUT/f"{item['id']}.log").write_text(result.stdout+result.stderr)
        if result.returncode: raise RuntimeError(f"{item['id']}: {result.stderr[-1200:]}")
    manifest = json.loads((folder/'island-live-v1.json').read_text())
    manifest.update(title=item['title'],titleES=item['title'],
        accent=artwork_accent(folder/'previews'/f"{item['id']}.gif"),
        previewURL=f"https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/{item['id']}.gif",
        posterURL=f"https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/{item['id']}.png")
    for ext in ('png','gif'):
        shutil.copy2(folder/'previews'/f"{item['id']}.{ext}",ROOT/'previews/island'/f"{item['id']}.{ext}")
    print(f"Ready: {item['title']} ({manifest['byteCount']} bytes)",flush=True)
    return manifest


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    themes = list(executor.map(build,items))
singularity = json.loads((ROOT/'catalogs/island-live-v1.json').read_text())
singularity.update(title='Singularity',titleES='Singularity',accent='#D9D9D9',
    previewURL='https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/singularity-live.gif',
    posterURL='https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/singularity-live.png')
(ROOT/'catalogs/island-gallery-v1.json').write_text(json.dumps(dict(schemaVersion=1,themes=[singularity]+themes),indent=2)+'\n')
print('Complete: 42 Live styles including Singularity',flush=True)

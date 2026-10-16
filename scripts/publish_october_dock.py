#!/usr/bin/env python3
"""Publish only the reviewed Dock batch. Never overwrite assets or app releases."""
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import urllib.request
from prepare_october_dock import OUT, batch, verify, write

REPO = 'leonardob8777-bit/Eagle-Gallery'
def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)
def api(path):
    return json.loads(gh('api', f'repos/{REPO}/{path}'))
def release_v9():
    return next(r for r in api('releases?per_page=100') if r['tag_name']=='v9')
def download(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Eagle-Gallery-QA'}), timeout=60) as r:
        assert r.status == 200
        return r.read()

def main():
    verify()
    before = json.loads((OUT/'before.json').read_text())
    assert json.loads((batch.REPO/'catalogs/dock-v1.json').read_text()) == before
    public = 'https://raw.githubusercontent.com/'+REPO+'/main/catalogs/dock-v1.json'
    assert json.loads(download(public+'?october=before')) == before
    entries = json.loads((OUT/'manifest.json').read_text())
    releases = api('releases?per_page=100')
    release = next((r for r in releases if r['tag_name']=='v9'), None)
    if release is None:
        gh('release','create','v9','--repo',REPO,'--draft','--latest=false',
           '--title','Dock Gallery · October Collection', '--notes',
           '31 new Dock backgrounds: 18 Static and 13 Live. Gallery content only; no Eagle app release. Existing themes remain unchanged. Packages keep the established 1146 × 318 format and SHA-256 checks.')
        release = release_v9()
    assets = {a['name']:a for a in release['assets']}
    def upload(entry):
        t=entry['theme']; p=OUT/'packages'/(t['id']+'.zip')
        if p.name in assets:
            assert assets[p.name]['digest']=='sha256:'+t['sha256']
        else:
            gh('release','upload','v9',str(p),'--repo',REPO)
        print('Uploaded '+p.name,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(upload, entries))
    assets={a['name']:a for a in release_v9()['assets']}
    for e in entries:
        t=e['theme']; a=assets[t['id']+'.zip']
        assert a['digest']=='sha256:'+t['sha256'] and a['size']==t['byteCount']
        assert a['state']=='uploaded'
    gh('release','edit','v9','--repo',REPO,'--draft=false','--latest=false')
    published = api('releases/tags/v9')
    assert not published['draft']
    public_assets = {a['name']:a for a in published['assets']}
    for e in entries:
        t=e['theme']; a=public_assets[t['id']+'.zip']
        assert a['browser_download_url']==t['packageURL']
    # Recheck immediately before staging, so another publisher cannot be overwritten.
    assert json.loads(download(public+'?october=prestage')) == before
    for p in (OUT/'previews').iterdir():
        dest=batch.REPO/'previews'/p.name
        assert not dest.exists(), 'Refusing preview overwrite'
        shutil.copyfile(p,dest)
    shutil.copyfile(OUT/'catalog.json',batch.REPO/'catalogs/dock-v1.json')
    write(batch.REPO/'metadata/october-2026.json',[
        dict(id=e['theme']['id'],sourceSHA256=e['sourceSHA256'],crop=e['crop'],
             kind='live' if e['theme']['frameCount']>1 else 'static') for e in entries])
    subprocess.run(['git','add','catalogs/dock-v1.json','metadata/october-2026.json',
                    'scripts/prepare_october_dock.py','scripts/publish_october_dock.py',
                    *[str(p.relative_to(batch.REPO)) for p in (batch.REPO/'previews').glob('october-dock-*')]],
                   cwd=batch.REPO,check=True)
    subprocess.run(['git','commit','-m','Add 18 Static and 13 Live October Dock backgrounds'],cwd=batch.REPO,check=True)
    subprocess.run(['git','push','origin','HEAD:main'],cwd=batch.REPO,check=True)
    write(OUT/'published-assets.json',dict(tag='v9',count=31,serverHashesMatch=True))

if __name__=='__main__': main()

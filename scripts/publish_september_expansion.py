#!/usr/bin/env python3
"""Explicit release-asset publication after offline verification. Never overwrite."""
import argparse
import concurrent.futures
import json
import subprocess
from prepare_september_expansion import OUT, digest, write_json

REPO='leonardob8777-bit/Eagle-Gallery'

def gh(*args):
    return subprocess.check_output(['gh',*args],text=True)

def api(endpoint):
    return json.loads(gh('api','repos/'+REPO+'/'+endpoint))

def publish(kind):
    folder=OUT/kind
    verified=json.loads((folder/'verified.json').read_text())
    assert not verified['nonMovingLive']
    entries=json.loads((folder/'manifest.json').read_text())
    tag='v8' if kind=='dock' else 'island-gifs-v1'
    releases=api('releases?per_page=100')
    release=next((r for r in releases if r['tag_name']==tag),None)
    if kind=='dock':
        if release is None:
            gh('release','create',tag,'--repo',REPO,'--draft','--title','Dock Gallery · September Collection',
               '--notes','62 new Dock backgrounds: 41 Live and 21 Static. Server-only content expansion for Eagle; no new IPA required. Existing styles remain unchanged. Packages retain the established 1146 × 318 geometry and verified SHA-256 hashes.')
            release=next(r for r in api('releases?per_page=100') if r['tag_name']==tag)
    assert release is not None
    def assets():
        values=[]
        for page in range(1,100):
            part=api(f'releases/{release["id"]}/assets?per_page=100&page={page}')
            values.extend(part)
            if len(part)<100:
                return {a['name']:a for a in values}
        raise RuntimeError('Unexpected asset pagination')
    existing=assets()
    before=list(existing.values())
    snapshot=folder/'release-assets-before.json'
    if not snapshot.exists():
        write_json(snapshot,before)
    def upload(entry):
        t=entry['theme']
        package=folder/'packages'/f'{t["id"]}.zip' if kind=='dock' else folder/t['id']/f'{t["id"]}-v1.zip'
        assert package.stat().st_size==t['byteCount'] and digest(package)==t['sha256']
        if package.name in existing:
            a=existing[package.name]
            assert a['digest']=='sha256:'+t['sha256'] and a['size']==t['byteCount'], 'Refusing asset overwrite'
        else:
            gh('release','upload',tag,str(package),'--repo',REPO)
        print('Uploaded '+package.name,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6 if kind=='island' else 3) as pool:
        list(pool.map(upload,entries))
    remote=assets()
    for entry in entries:
        t=entry['theme']
        name=t['packageURL'].rsplit('/',1)[-1]
        a=remote[name]
        assert a['digest']=='sha256:'+t['sha256'] and a['size']==t['byteCount'] and a['state']=='uploaded'
    for a in before:
        assert remote[a['name']]['id']==a['id'] and remote[a['name']]['digest']==a['digest']
    if release['draft']:
        assert kind=='dock'
        gh('release','edit',tag,'--repo',REPO,'--draft=false')
    assert not api('releases/tags/'+tag)['draft']
    write_json(folder/'remote-assets-verified.json',dict(tag=tag,verified=len(entries),
        hashesMatch=True,existingAssetsUnchanged=True))
    print(f'PUBLIC and verified: {kind}, {len(entries)} packages',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('gallery',choices=['dock','island'])
    publish(parser.parse_args().gallery)

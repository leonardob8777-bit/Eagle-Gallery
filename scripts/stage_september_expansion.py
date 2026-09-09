#!/usr/bin/env python3
"""Install verified, already-public candidates into this repo without committing."""
import json
import shutil
from prepare_september_expansion import ROOT, OUT, configured_records, write_json

def stage():
    metadata={'schemaVersion':1,'batch':'2026-09-08','serverOnly':True,'dock':[],'island':[]}
    for kind in ('dock','island'):
        folder=OUT/kind
        offline=json.loads((folder/'verified.json').read_text())
        remote=json.loads((folder/'remote-assets-verified.json').read_text())
        assert remote['hashesMatch'] and remote['verified']==offline['added']
        assert not offline['nonMovingLive']
        before=json.loads((OUT/f'{kind}-before.json').read_text())
        target=ROOT/'catalogs'/('dock-v1.json' if kind=='dock' else 'island-gallery-v1.json')
        current=json.loads(target.read_text())
        candidate=json.loads((folder/'catalog.json').read_text())
        assert current==before or current==candidate,'Concurrent catalog edit; refusing overwrite'
        assert candidate['themes'][:len(before['themes'])]==before['themes']
        entries=json.loads((folder/'manifest.json').read_text())
        for entry in entries:
            t=entry['theme']
            src=folder/'previews' if kind=='dock' else folder/t['id']/'previews'
            dst=ROOT/'previews' if kind=='dock' else ROOT/'previews/island'
            for ext in (['png','gif'] if t['frameCount']>1 else ['png']):
                source=src/f'{t["id"]}.{ext}'
                dest=dst/source.name
                assert not dest.exists() or dest.read_bytes()==source.read_bytes(),'Preview collision'
                shutil.copy2(source,dest)
            record=entry['record'] if kind=='island' else entry
            metadata[kind].append(dict(id=t['id'],title=t['title'],sourceSHA256=record['sourceSHA256'],
                **({'dockID':record['dockID'],'kind':record['kind'],'cropAnchor':record['cropAnchor']} if kind=='island'
                else {'kind':'live' if t['frameCount']==17 else 'static'})))
        write_json(target,candidate)
    chosen={r['dockID'] for r in metadata['island']}
    skipped=json.loads((OUT/'island-skipped.json').read_text())
    existing={r['id']:r['reason'] for r in skipped}
    existing.update({id:'already-bundled-in-island' for id in ['bubblegum','duck-mood','blue-screen','walking-flame']})
    candidates=json.loads((OUT/'candidates.json').read_text())+configured_records()
    metadata['review']=[dict(dockID=r['id'],decision='selected' if r['id'] in chosen else
        existing[r['id']] if r['id'] in existing else 'not-selected-for-small-island') for r in candidates]
    assert len(metadata['review'])==490 and len({r['dockID'] for r in metadata['review']})==490
    write_json(ROOT/'metadata/september-2026.json',metadata)
    print(f"Staged {len(metadata['dock'])} Dock + {len(metadata['island'])} Island additions; all 490 reviewed")

if __name__=='__main__':
    stage()

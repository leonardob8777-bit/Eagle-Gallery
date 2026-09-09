#!/usr/bin/env python3
"""Exhaustive candidate checks; no server or application mutations."""
import argparse
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
from prepare_september_expansion import ROOT, OUT, VORTEX, digest, write_json

def swift_contracts():
    app=ROOT.parent/'Eagle-Beta11/lara/views/new'
    island=(app/'IslandLiveMedia.swift').read_text()
    definitions=island[island.index('nonisolated struct IslandLiveManifest'):island.index('/// An isolated, on-demand Island package.')]
    definitions=definitions.replace('private nonisolated struct IslandLiveCatalog','nonisolated struct IslandLiveCatalog')
    dock=(app/'DockGalleryView.swift').read_text()
    dock_definitions=dock[dock.index('private struct RemoteDockGalleryCatalog'):dock.index('    var localizedTitle:',dock.index('private struct RemoteDockGalleryTheme'))]+'}\n'
    dock_definitions=dock_definitions.replace('private struct','struct')
    predicate=dock[dock.index('    private static func isSupported(_ theme: RemoteDockGalleryTheme)'):dock.index('    private static func validFrames')]
    predicate=predicate.replace('private static func','func')
    code='import Foundation\n'+definitions+dock_definitions+predicate+f'''
let island = try JSONDecoder().decode(IslandLiveCatalog.self, from: Data(contentsOf: URL(fileURLWithPath: "{OUT}/island/catalog.json")))
let dock = try JSONDecoder().decode(RemoteDockGalleryCatalog.self, from: Data(contentsOf: URL(fileURLWithPath: "{OUT}/dock/catalog.json")))
precondition(island.isSupported)
precondition(dock.schemaVersion == 1 && dock.themes.allSatisfy(isSupported))
print("PASS actual Eagle Swift validators: \\(dock.themes.count) Dock, \\(island.themes.count) Island")
'''
    result=subprocess.run(['xcrun','swift','-'],input=code,text=True,capture_output=True,timeout=120)
    print(result.stdout+result.stderr,flush=True)
    assert result.returncode==0

def review_partial():
    records=json.loads((OUT/'island-selection.json').read_text())
    ready=[r for r in records if (OUT/'island'/r['id']/'verification.json').exists()]
    for start in range(0,len(ready),48):
        sheet=Image.new('RGB',(1440,800),'#16161a')
        draw=ImageDraw.Draw(sheet)
        for offset,record in enumerate(ready[start:start+48]):
            path=OUT/'island'/record['id']/'previews'/f"{record['id']}.gif"
            with Image.open(path) as im:
                im.seek(im.n_frames//2)
                thumb=im.convert('RGBA')
                thumb=thumb.crop(thumb.getbbox())
                thumb.thumbnail((232,80))
                x,y=offset%6*240,offset//6*100
                sheet.paste(thumb,(x,y),thumb)
                draw.text((x+3,y+80),f"{start+offset+1:03} {record['title'][:29]}",fill='white')
        sheet.save(OUT/'island'/f'preliminary-{start//48+1}.jpg')
    print(f'Review: {len(ready)} ready')

def verify(kind):
    folder = OUT/kind
    catalog = json.loads((folder/'catalog.json').read_text())
    before = json.loads((OUT/f'{kind}-before.json').read_text())
    assert catalog['schemaVersion']==1
    assert catalog['themes'][:len(before['themes'])]==before['themes'], 'Existing themes changed'
    assert len({t['id'] for t in catalog['themes']})==len(catalog['themes'])
    assert (folder/'catalog.json').stat().st_size <= (512*1024 if kind=='dock' else 2*1024*1024)
    if kind=='island':
        assert len(catalog['themes'])<=500
    manifests = json.loads((folder/'manifest.json').read_text())
    alpha = Image.open(VORTEX).getchannel('A').tobytes()
    frames_checked = 0
    no_motion = []
    for batch_index, entry in enumerate(manifests,1):
        theme = entry['theme']
        is_island = kind=='island'
        source = entry['record'] if is_island else entry
        assert digest(Path(source['source']))==source['sourceSHA256']
        assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',theme['id'])
        assert 0<len(theme['title'])<=80 and 0<len(theme['titleES'])<=80
        assert re.fullmatch(r'#[0-9a-fA-F]{6}',theme['accent'])
        package = folder/theme['id']/f"{theme['id']}-v1.zip" if is_island else folder/'packages'/f"{theme['id']}.zip"
        assert package.stat().st_size==theme['byteCount']<= (34 if is_island else 30)*1024*1024
        assert digest(package)==theme['sha256']
        assert (theme['width'],theme['height'])==((1200,500) if is_island else (1146,318))
        assert (theme['frameCount'],theme['fps']) in ([(17,6)] if is_island else [(17,6),(1,1)])
        expected_url = (f'https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/island-gifs-v1/{theme["id"]}-v1.zip'
            if is_island else f'https://github.com/leonardob8777-bit/Eagle-Gallery/releases/download/v8/{theme["id"]}.zip')
        assert theme['packageURL']==expected_url
        pixel_hashes = []
        with zipfile.ZipFile(package) as archive:
            assert archive.testzip() is None
            assert set(archive.namelist())=={f'frame{i:02d}.png' for i in range(1,theme['frameCount']+1)}
            for i in range(1,theme['frameCount']+1):
                data = archive.read(f'frame{i:02d}.png')
                with Image.open(io.BytesIO(data)) as frame:
                    assert frame.format=='PNG'
                    assert frame.size==(theme['width'],theme['height'])
                    assert frame.mode==('RGBA' if is_island else 'RGB')
                    if is_island:
                        assert len(data)<=2*1024*1024
                        assert frame.getchannel('A').tobytes()==alpha
                        assert hashlib.sha256(data).hexdigest()==theme['frameSHA256'][i-1]
                    pixel_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
                frames_checked+=1
        if is_island and source['kind']=='static':
            assert len(set(pixel_hashes))==1, 'A fixed image must not animate'
        elif theme['frameCount']>1 and len(set(pixel_hashes))==1:
            no_motion.append(theme['id'])
        previews = folder/theme['id']/'previews' if is_island else folder/'previews'
        with Image.open(previews/f"{theme['id']}.png") as im:
            assert im.size==(theme['width'],theme['height'])
        if theme['frameCount']>1:
            with Image.open(previews/f"{theme['id']}.gif") as im:
                assert im.size==((600,250) if is_island else (573,159))
                duration = 0
                for i in range(im.n_frames):
                    im.seek(i)
                    duration += im.info.get('duration',0)
                assert abs(duration-17/6*1000)<25,(theme['id'],duration)
        if is_island:
            base='https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/island/'
            assert theme['previewURL']==base+theme['id']+'.gif'
            assert theme['posterURL']==base+theme['id']+'.png'
        if batch_index%16==0:
            print(f'Verified {kind}: {batch_index}/{len(manifests)} packages, {frames_checked} frames',flush=True)
    # Render small native-mask previews, not large original images, for final visual review.
    for start in range(0,len(manifests),48):
        sheet=Image.new('RGB',(1440,800),'#16161a')
        draw=ImageDraw.Draw(sheet)
        for offset, entry in enumerate(manifests[start:start+48]):
            t=entry['theme']
            previews=folder/t['id']/'previews' if kind=='island' else folder/'previews'
            ext='gif' if t['frameCount']>1 else 'png'
            with Image.open(previews/f"{t['id']}.{ext}") as im:
                im.seek(getattr(im,'n_frames',1)//2)
                thumb=im.convert('RGBA')
                if kind=='island':
                    thumb=thumb.crop(thumb.getbbox())
                thumb.thumbnail((232,80))
                x,y=offset%6*240,offset//6*100
                sheet.paste(thumb,(x,y),thumb)
                draw.text((x+3,y+80),f"{start+offset+1:03} {t['title'][:29]}",fill='white')
        sheet.save(folder/f'review-{start//48+1}.jpg')
    report=dict(gallery=kind,added=len(manifests),total=len(catalog['themes']),
        framesVerified=frames_checked,originalsUnchanged=True,existingEntriesUnchanged=True,
        bytes=sum(e['theme']['byteCount'] for e in manifests),nonMovingLive=no_motion)
    write_json(folder/'verified.json',report)
    print(json.dumps(report,indent=2),flush=True)
    assert not no_motion,'Review animations without movement before publishing'

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('gallery',choices=['dock','island','swift','review'])
    kind=parser.parse_args().gallery
    if kind=='swift': swift_contracts()
    elif kind=='review': review_partial()
    else: verify(kind)

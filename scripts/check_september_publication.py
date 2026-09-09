#!/usr/bin/env python3
"""Check the published catalogs, every new preview, and sample public downloads."""
import concurrent.futures
import hashlib
import json
import subprocess
import time
import urllib.request
from prepare_september_expansion import ROOT, OUT, write_json

def request(url, method='GET'):
    error=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method=method),timeout=45) as response:
                assert response.status==200
                return response.read() if method=='GET' else dict(response.headers)
        except Exception as e:
            error=e
            if attempt<2: time.sleep(2)
    raise RuntimeError(url) from error

def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==commit
    checks=[]
    samples=[]
    for kind in ('dock','island'):
        name='dock-v1.json' if kind=='dock' else 'island-gallery-v1.json'
        local=(ROOT/'catalogs'/name).read_bytes()
        base='https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/'
        assert request(base+commit+'/catalogs/'+name)==local
        app_url=base+'main/catalogs/'+name+('?catalog=21' if kind=='dock' else '')
        actual=request(app_url)
        assert actual==local, 'App URL still serves a cached catalog; retry after CDN propagation'
        entries=json.loads((OUT/kind/'manifest.json').read_text())
        for entry in entries:
            t=entry['theme']
            urls=[t['previewURL'],t['posterURL']] if kind=='island' else [t['previewURL']]+([t['animatedPreviewURL']] if 'animatedPreviewURL' in t else [])
            for url in urls:
                checks.append(url)
        for motion in ('live','static'):
            subset=[e for e in entries if (e['record']['kind'] if kind=='island' else 'live' if e['theme']['frameCount']>1 else 'static')==motion]
            samples.append(max(subset,key=lambda e:e['theme']['byteCount'])['theme'])
    def check_preview(url):
        h=request(url,'HEAD')
        content_type=h.get('Content-Type',h.get('content-type',''))
        assert content_type.split(';')[0] in ('image/png','image/gif','application/octet-stream'),(url,content_type)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(check_preview,checks))
    for theme in samples:
        data=request(theme['packageURL'])
        assert len(data)==theme['byteCount'] and hashlib.sha256(data).hexdigest()==theme['sha256']
        print('Public download matches: '+theme['id'],flush=True)
    report=dict(commit=commit,catalogs=2,previews=len(checks),publicPackageSamples=len(samples),
        exactAppURLsCurrent=True,allPublicAssetsPreviouslyHashVerified=True)
    write_json(OUT/'public-verification.json',report)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Read-only checks against public gallery URLs and GitHub asset checksums."""
import concurrent.futures
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def request(url, method="GET"):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "Eagle-Gallery-QA"})
            with urllib.request.urlopen(req, timeout=45) as response:
                assert response.status == 200, (url, response.status)
                return response.read() if method == "GET" else None
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def main():
    expected = json.loads((REPO / "catalogs/dock-v1.json").read_text())
    url = "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/catalogs/dock-v1.json"
    actual = json.loads(request(url + "?qa=twigal-v3"))
    assert actual == expected, "Public catalog differs from local catalog"
    themes = [t for t in actual["themes"] if t["id"].startswith("twigal")]
    assert len(actual["themes"]) == 86 and len(themes) == 69
    release = json.loads(subprocess.check_output([
        "gh", "api", "repos/leonardob8777-bit/Eagle-Gallery/releases/tags/v3"]))
    assert not release["draft"]
    assets = {a["name"]: a for a in release["assets"]}
    assert len(assets) == 69
    for theme in themes:
        asset = assets[theme["id"] + ".zip"]
        assert asset["state"] == "uploaded"
        assert asset["size"] == theme["byteCount"]
        assert asset["digest"] == "sha256:" + theme["sha256"]
        assert asset["browser_download_url"] == theme["packageURL"]
    print("PASS: public catalog (86 themes), 69 release sizes and SHA-256 checksums", flush=True)

    def check(theme):
        for key in ("previewURL", "animatedPreviewURL"):
            if key not in theme:
                continue
            data = request(theme[key])
            local = REPO / "previews" / theme[key].rsplit("/", 1)[-1]
            assert hashlib.sha256(data).digest() == hashlib.sha256(local.read_bytes()).digest()
        request(theme["packageURL"], "HEAD")
        return theme["id"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for n, _ in enumerate(pool.map(check, themes), 1):
            if n % 10 == 0 or n == 69:
                print(f"PASS: public previews and download links {n}/69", flush=True)
    print("PUBLICATION VERIFIED", flush=True)


if __name__ == "__main__":
    main()

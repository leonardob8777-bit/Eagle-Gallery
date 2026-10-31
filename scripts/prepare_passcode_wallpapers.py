#!/usr/bin/env python3
"""Render the visual backgrounds of Eagle's nine HTML concepts as wallpapers.

Requires Pillow and Playwright Chromium. Hides the imitation passcode controls
before capture. Packages each still with Eagle's LayeredAnimation descriptor
layout so its existing .tendies importer can install the background separately.
"""

import base64
import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import uuid
import zipfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "passcode" / "live"
PACKAGES = ROOT / "wallpapers" / "packages"
PREVIEWS = ROOT / "previews" / "wallpapers"
CATALOG = ROOT / "catalogs" / "wallpaper-v1.json"
PASSCODE_CATALOG = ROOT / "catalogs" / "passcode-v1.json"
WIDTH, HEIGHT = 1170, 2532
PROVIDER_INFO = base64.b64decode(
    "YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGmCwwVFhogVSRudWxs0w0ODxASFFdOUy5rZXlzWk5TLm9iamVjdHNWJGNsYXNzoRGAAqETgAOABV8QHGtDb25maWd1cmF0aW9uTGFzdFVzZURhdGVLZXnSFw8YGVdOUy50aW1lI0HGwARI1HUUgATSGxwdHlokY2xhc3NuYW1lWCRjbGFzc2VzVk5TRGF0ZaIdH1hOU09iamVjdNIbHCEiXxATTlNNdXRhYmxlRGljdGlvbmFyeaMjJB9fEBNOU011dGFibGVEaWN0aW9uYXJ5XE5TRGljdGlvbmFyeQAIABEAGgAkACkAMgA3AEkATABRAFMAWgBgAGcAbwB6AIEAgwCFAIcAiQCLAKoArwC3AMAAwgDHANIA2wDiAOUA7gDzAQkBDQEjAAAAAAAAAgEAAAAAAAAAJQAAAAAAAAAAAAAAAAAAATA="
)
ASSET_MANIFEST = b'<?xml version="1.0" encoding="UTF-8"?>\n<caml xmlns="http://www.apple.com/CoreAnimation/1.0"><MicaAssetManifest><modules type="NSArray"/></MicaAssetManifest></caml>\n'


def plist(value: object) -> bytes:
    return plistlib.dumps(value, fmt=plistlib.FMT_XML, sort_keys=False)


def index_xml() -> bytes:
    return plist({
        "assetManifest": "assetManifest.caml",
        "documentHeight": float(HEIGHT),
        "documentResizesToView": True,
        "documentWidth": float(WIDTH),
        "dynamicGuidesEnabled": True,
        "geometryFlipped": False,
        "guidesEnabled": True,
        "interactiveMouseEventsEnabled": True,
        "interactiveShowsCursor": True,
        "interactiveTouchEventsEnabled": False,
        "loopEnd": 0.0,
        "loopStart": 0.0,
        "loopingEnabled": False,
        "multitouchDisablesMouse": False,
        "multitouchEnabled": False,
        "presentationMouseEventsEnabled": True,
        "presentationShowsCursor": True,
        "presentationTouchEventsEnabled": False,
        "rootDocument": "main.caml",
        "savesWindowFrame": False,
        "scalesToFitInPlayer": True,
        "showsTouches": True,
        "snappingEnabled": True,
        "timelineMarkers": "[(null)]",
        "touchesColor": "1 1 0 0.8",
        "unitsInPixelsInPlayer": True,
    })


def states() -> str:
    return """<states><LKState name="Locked"><elements/></LKState><LKState name="Unlock"><elements/></LKState><LKState name="Sleep"><elements/></LKState></states><stateTransitions><LKStateTransition fromState="*" toState="Unlock"><elements/></LKStateTransition><LKStateTransition fromState="Unlock" toState="*"><elements/></LKStateTransition><LKStateTransition fromState="*" toState="Locked"><elements/></LKStateTransition><LKStateTransition fromState="Locked" toState="*"><elements/></LKStateTransition><LKStateTransition fromState="*" toState="Sleep"><elements/></LKStateTransition><LKStateTransition fromState="Sleep" toState="*"><elements/></LKStateTransition></stateTransitions>"""


def background_caml() -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<caml xmlns="http://www.apple.com/CoreAnimation/1.0">
  <CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" hidden="0" name="_FLOATING" position="{WIDTH // 2} {HEIGHT // 2}">
    <sublayers><CATransformLayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" allowsHitTesting="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" name="Eagle Background" position="{WIDTH // 2} {HEIGHT // 2}">
      <sublayers><CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" name="Eagle Still" position="{WIDTH // 2} {HEIGHT // 2}">
        <contents type="CGImage" src="assets/0.jpg"/>
        <animations><animation type="CAKeyframeAnimation" calculationMode="linear" keyPath="contents" beginTime="1e-100" duration="8" removedOnCompletion="0" repeatCount="inf" repeatDuration="0" speed="1" timeOffset="0" autoreverses="0"><values><CGImage src="assets/0.jpg"/><CGImage src="assets/1.jpg"/></values></animation></animations>
      </CALayer></sublayers></CATransformLayer></sublayers>{states()}
  </CALayer>
</caml>'''.encode()


def floating_caml(has_subject: bool = False) -> bytes:
    if has_subject:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<caml xmlns="http://www.apple.com/CoreAnimation/1.0"><CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" hidden="0" name="_FLOATING" position="{WIDTH // 2} {HEIGHT // 2}"><sublayers><CATransformLayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" name="Eagle Depth" position="{WIDTH // 2} {HEIGHT // 2}"><sublayers><CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" name="Eagle Subject" position="{WIDTH // 2} {HEIGHT // 2}"><contents type="CGImage" src="assets/subject.png"/></CALayer></sublayers></CATransformLayer></sublayers>{states()}</CALayer></caml>'''.encode()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<caml xmlns="http://www.apple.com/CoreAnimation/1.0"><CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" bounds="0 0 {WIDTH} {HEIGHT}" contentsFormat="RGBA8" cornerCurve="circular" hidden="0" name="_BACKGROUND" position="{WIDTH // 2} {HEIGHT // 2}"><sublayers><CALayer allowsEdgeAntialiasing="1" allowsGroupOpacity="1" anchorPoint="0 0" bounds="0 0 0 0" contentsFormat="RGBA8" cornerCurve="circular" name="_CENTER_BACKGROUND" position="{WIDTH // 2} {HEIGHT // 2}"/></sublayers>{states()}</CALayer></caml>'''.encode()


def zip_entry(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2026, 10, 31, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_package(
    identifier: str,
    title: str,
    image: Image.Image,
    *,
    foreground_png: bytes | None = None,
    version: int = 1,
) -> Path:
    jpg = io.BytesIO()
    image.convert("RGB").save(jpg, format="JPEG", quality=88, optimize=True, subsampling=0)
    image_data = jpg.getvalue()
    package = PACKAGES / f"{identifier}-v{version}.tendies"
    descriptor_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "eagle-background:" + identifier)).upper()
    numeric_id = int.from_bytes(hashlib.sha256(identifier.encode()).digest()[:3], "big") % 800_000 + 100_000
    descriptor = f"descriptors/{descriptor_id}/"
    contents = descriptor + "versions/1/contents/"
    wallpaper_name = "9183.Eagle-810w-1080h@2x~ipad.wallpaper"
    background_name = "9183.Eagle_Background-810w-1080h@2x~ipad.ca"
    floating_name = "9183.Eagle_Floating-810w-1080h@2x~ipad.ca"
    wall = contents + wallpaper_name + "/"
    background = wall + background_name + "/"
    floating = wall + floating_name + "/"
    wallpaper_plist = {
        "appearanceAware": True,
        "assets": {"lockAndHome": {"default": {
            "backgroundAnimationFileName": background_name,
            "floatingAnimationFileNameKey": floating_name,
            "identifier": numeric_id,
            "name": title,
            "type": "LayeredAnimation",
        }}},
        "contentVersion": 2.01,
        "family": "Eagle",
        "identifier": numeric_id,
        "logicalScreenClass": "810w-1080h@2x~ipad",
        "name": title,
        "preferredProminentColor": {"dark": "#000000", "default": "#FFFFFF"},
        "version": 1,
    }
    files = {
        descriptor + "com.apple.posterkit.provider.descriptor.identifier": str(numeric_id).encode(),
        descriptor + "com.apple.posterkit.role.identifier": b"PRPosterRoleLockScreen",
        descriptor + "providerInfo.plist": PROVIDER_INFO,
        contents + "com.apple.posterkit.provider.contents.userInfo": plist({
            "posterEnvironmentOverrides": b"{}",
            "wallpaperRepresentingFileName": wallpaper_name,
            "wallpaperRepresentingIdentifier": numeric_id,
        }),
        wall + "Wallpaper.plist": plist(wallpaper_plist),
        background + "assetManifest.caml": ASSET_MANIFEST,
        background + "index.xml": index_xml(),
        background + "main.caml": background_caml(),
        background + "assets/0.jpg": image_data,
        background + "assets/1.jpg": image_data,
        floating + "assetManifest.caml": ASSET_MANIFEST,
        floating + "index.xml": index_xml(),
        floating + "main.caml": floating_caml(foreground_png is not None),
    }
    if foreground_png is not None:
        files[floating + "assets/subject.png"] = foreground_png
    with zipfile.ZipFile(package, "w") as archive:
        for path, data in sorted(files.items()):
            zip_entry(archive, path, data)
    return package


def prepare_html(raw: str) -> str:
    return re.sub(
        r'(<div[^>]*>)(\s*<sc-for list="\{\{dots\}\}")',
        lambda match: match.group(1).replace("<div", "<div data-eagle-dots", 1) + match.group(2),
        raw,
    )


def main() -> None:
    from playwright.sync_api import sync_playwright

    catalog = json.loads(CATALOG.read_text())
    passcode = json.loads(PASSCODE_CATALOG.read_text())
    assert len(passcode["themes"]) == 9
    existing = catalog["wallpapers"]
    if existing:
        assert {entry["id"] for entry in existing} == {theme["id"] for theme in passcode["themes"]}
        assert all(
            entry["url"].startswith(
                "https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/wallpapers/packages/"
            )
            for entry in existing
        ), "refusing to overwrite unrelated wallpaper entries"
    catalog["wallpapers"] = []
    PACKAGES.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=3,
            reduced_motion="no-preference",
        )
        page.route("https://**", lambda route: route.abort())
        for theme in passcode["themes"]:
            identifier, title = theme["id"], theme["name"]
            page.set_content(prepare_html((SOURCE / f"{identifier}.html").read_text()), wait_until="load")
            page.add_style_tag(content="button,input,textarea,p,h1,h2,h3,header,footer,[data-eagle-dots] { visibility:hidden !important; }")
            page.evaluate("""() => { const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);for(const node of nodes){if(/PASS>|ENTER CODE|ENTER PASSCODE|INSERT CODE/i.test(node.nodeValue))node.nodeValue='';} }""")
            page.wait_for_timeout(350)
            preview = PREVIEWS / f"{identifier}.png"
            page.screenshot(path=str(preview), full_page=False, animations="allow")
            image = Image.open(preview)
            assert image.size == (WIDTH, HEIGHT), identifier
            package = build_package(identifier, title, image)
            catalog["wallpapers"].append({
                "id": identifier,
                "name": title,
                "description": "Fondo estático del diseño Eagle. Los números se aplican por separado en Passcode.",
                "authors": "Eagle",
                "preview": f"https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/previews/wallpapers/{identifier}.png",
                "url": f"https://raw.githubusercontent.com/leonardob8777-bit/Eagle-Gallery/main/wallpapers/packages/{package.name}",
                "byteCount": package.stat().st_size,
                "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                "minimumIOSMajor": 17,
            })
            print(identifier, package.stat().st_size)
        browser.close()
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

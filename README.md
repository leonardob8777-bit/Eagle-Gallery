# Eagle Gallery

Remote artwork catalog for Eagle. Packages contain the original PNG frames and
are published without image recompression. The app verifies package size,
SHA-256, frame count, and exact dimensions before caching or applying a theme.

## September expansion (2026-09-08)

- Dock: 62 new backgrounds (41 Live and 21 Static), for 490 remote styles total.
- Island: 208 additions selected from the full Dock collection, including the
  new backgrounds. The selection favors patterns, flowing light, textures and
  compositions that remain clear at Island size. Small text, poorly fitting
  portraits and weak perimeter detail were excluded after visual review.
- Island additions contain 109 animations and 99 fixed artworks, for 250 remote
  styles total. Eagle 1.0.4 only loads remote Island content in its Live section;
  both types appear there. Fixed artworks repeat an identical frame and do not
  animate. The app's bundled Static section is unchanged.
- This is a server-only content update: no new IPA, app code, native geometry,
  previously published themes, or existing packages are changed.

Dock packages are hosted in `v8`. New Island packages use the existing
`island-gifs-v1` release required by Eagle 1.0.4's URL validation. Island keeps
the exact Vortex alpha mask on a 1200 × 500 canvas, 17 frames at 6 FPS, archive
SHA-256 and 17 per-frame hashes. Packages download on demand, not with the app.

`metadata/september-2026.json` records the additions, source hashes, Island crop
anchors and a review decision for all 490 Dock candidates. Detailed build
manifests and local source-path inventories remain outside this repository.

Preparation and publication are separate commands:

1. `prepare_september_expansion.py` inventories sources, prepares Dock, renders
   candidate contact sheets, selects Island artwork and builds the packages.
2. `verify_september_expansion.py` checks every frame and source, renders small
   previews, and runs the actual Eagle Swift catalog validators on the candidates.
3. `publish_september_expansion.py` uploads without replacing existing assets
   and verifies every public asset's server-side SHA-256 and byte count.
4. `stage_september_expansion.py` installs the candidates only after offline
   and public-asset checks. Catalogs and previews are then committed together.

## TwiGal batch (2026-09-05)

`scripts/prepare_twigal_batch.py SOURCE OUTPUT` prepares 68 videos and one static
image without changing their originals or the application's Dock geometry.
It writes a candidate catalog, packages, previews, source hashes, and review
contact sheets to a new output directory. It does not publish automatically.

- Application frames: 1146 × 318 RGB PNG, aspect-fill with a centered crop.
- Videos: 17 frames at 6 FPS, matching the existing app contract. Long clips use
  the opening 17-frame sequence; short clips repeat at their source speed.
- Static image: one frame at 1 FPS.
- No baked corner mask, colored padding, or resizing of the native Dock.
- Animated gallery previews: 573 × 159 looping GIFs, as in the existing gallery.
- Packages must pass frame/dimension checks and remain below the app's 30 MiB
  limit. Their compressed size and SHA-256 are recorded in the catalog.

Release assets must be uploaded and made public before publishing the candidate
catalog and previews. Existing catalog entries are preserved unchanged.

## Static / Live batch (2026-09-05)

`scripts/prepare_mixed_batch.py SOURCE OUTPUT` prepares the `fotosvideos`
collection: 39 static images, 37 animated GIFs, and 2 videos. This brings the
catalog to 182 styles (46 Static and 136 Live). The v6 packages use the same
dimensions, frame rate, and native-mask contract as the existing collection.
Selected vertical crops keep faces visible without adding padding or changing
the Dock shape. GIF previews preserve timing when identical frames are merged.
The output manifest records source hashes and crop anchors for reproducibility.
Media remains remotely hosted; none of this batch is embedded in the IPA.

## Island Live pilot

`scripts/prepare_island_live.py VIDEO VORTEX_PNG OUTPUT` creates the first
Island-only animation, Singularity. Each of its 17 frames has the exact
1200 × 500 canvas and byte-identical alpha channel of the existing Vortex
asset. Only the RGB artwork inside that mask changes; native geometry is not
part of this package. The video is sampled at the established 6 FPS rate.

`catalogs/island-live-v1.json` describes the independent `island-v1` release,
including archive and per-frame SHA-256 hashes. This pilot does not modify the
Dock catalog or its packages. The app verifies all frames before applying,
uses one still frame under Reduce Motion, and retains the existing Island
replacement/removal transaction. Real-device visual acceptance is a separate
step from build and package validation.

## More collection (2026-09-05)

`scripts/prepare_more_batch.py SOURCE OUTPUT` prepares the mixed `more`
collection without changing its originals. The v7 release adds 186 Static and
60 Live styles, bringing Dock Gallery to 428 styles. Every generated frame is
an RGB PNG at 1146 × 318 with a full-bleed aspect-fill crop; Live styles retain
the established 17-frame, 6 FPS contract. Packages remain online and download
only when selected, so the new artwork is not embedded in Eagle's IPA.

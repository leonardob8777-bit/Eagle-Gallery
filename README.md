# Eagle Gallery

Remote artwork catalog for Eagle. Packages contain the original PNG frames and
are published without image recompression. The app verifies package size,
SHA-256, frame count, and exact dimensions before caching or applying a theme.

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

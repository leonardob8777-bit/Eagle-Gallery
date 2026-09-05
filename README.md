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

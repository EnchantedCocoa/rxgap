# Vendored dependencies — RxGap

Vendored for a no-build-step web app. All assets are served locally from
`app/vendor/`. No package manager, no CDN runtime dependency for the library
itself (map tiles are still fetched from the basemap provider at runtime).

## MapLibre GL JS

- **Version:** `5.24.0` (pinned — latest stable v5.x at vendoring time; v6.x
  exists but the task targets v5.x)
- **Source CDN:** unpkg (mirror of the npm package)
- **License:** 3-Clause BSD (see `LICENSE.txt`)

| File | Source URL | Size (bytes) | sha256 |
|------|------------|--------------|--------|
| `maplibre-gl.js`  | https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.js  | 1056837 | `45a9b07a9189ce56054c620a947ccf41e291e58c95e9b61533b740aaa65ee5cb` |
| `maplibre-gl.css` | https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.css | 70024   | `ab1e70d59ec40465bae7e7030da2f3ccf28133fd502e62bd598eefbadfd7a732` |
| `LICENSE.txt`     | https://unpkg.com/maplibre-gl@5.24.0/LICENSE.txt          | 5984    | `ee5fc05a0677eaf69601d2c7db0d9ecd6cc27c3abc1d0733bc9ed34707cf8ef2` |

JS banner confirms the pinned build:
`/** MapLibre GL JS @license 3-Clause BSD ... /v5.24.0/LICENSE.txt */`

## Base map

- **Chosen:** OpenFreeMap — `positron` style (muted light, vector)
- **Style URL fetched:** https://tiles.openfreemap.org/styles/positron
- **Saved locally as:** `basemap-style.json` (25153 bytes, style spec v8)

### Why this one

Two candidates were fetched and verified (both HTTP 200, valid v8 JSON, with
tile/glyph/sprite endpoints individually probed and all returning 200):

| | OpenFreeMap positron (**chosen**) | CARTO Positron (fallback) |
|---|---|---|
| API key | none | none |
| Registration | none | none |
| Usage limits | **none** (explicitly unlimited, self-hosted OSM) | fair-use / soft limits, not guaranteed for production |
| Visual | muted light "Positron" | muted light "Positron" |
| Data | OpenStreetMap + OpenMapTiles + Natural Earth | OpenStreetMap + Protomaps via CARTO |

For a public civic-data hackathon demo the decisive factor is **no key and no
rate limits** — OpenFreeMap guarantees both, so a live demo cannot be throttled
or require an account. Both styles are the same muted-light look suitable for
data overlays. CARTO Positron is a drop-in fallback if OpenFreeMap is ever
unreachable (swap the style URL; its attribution differs, see below).

### Verification performed

- Style JSON: HTTP 200, valid JSON, spec `version: 8`.
- Sources: `openmaptiles` (TileJSON `https://tiles.openfreemap.org/planet`,
  HTTP 200) and `ne2_shaded` raster (sample tile HTTP 200).
- Glyphs: `.../fonts/{fontstack}/{range}.pbf` sample HTTP 200.
- Sprite: `.../sprites/ofm_f384/ofm.json` HTTP 200.

### Required attribution (MUST be displayed)

OpenFreeMap carries attribution in the source TileJSON, not the style root, so
MapLibre's default `AttributionControl` surfaces it automatically. If
attribution is rendered manually, use:

> OpenFreeMap © OpenMapTiles Data from OpenStreetMap

HTML form (from the TileJSON `attribution` field):

```
<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>
```

CARTO fallback attribution (if that style is used instead):

```
&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/about-carto/">CARTO</a>
```

## Smoke test

`$KIROCREW_SCRATCH/maplibre_test.html` loads the vendored JS/CSS and
`basemap-style.json` via absolute `file://` paths, centered on Boston
(`[-71.06, 42.32]`, zoom 11). It is a syntax/load confirmation only (no browser
was opened). File-level checks passed: JS non-empty + correct banner, CSS
non-empty, style.json valid.

## Notes / caveats

- Map tiles, glyphs, and sprites are still fetched from
  `tiles.openfreemap.org` at runtime — the map needs network access. Only the
  MapLibre library itself is fully local.
- `basemap-style.json` embeds absolute `https://tiles.openfreemap.org/...` URLs
  for its sources/glyphs/sprite; it does not need rewriting to work.

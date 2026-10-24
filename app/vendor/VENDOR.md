# Vendored front-end files

| File | Version | Source | sha256 |
|---|---|---|---|
| `leaflet.js` | Leaflet 1.9.4 | https://unpkg.com/leaflet@1.9.4/dist/leaflet.js | `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a` |
| `leaflet.css` | Leaflet 1.9.4 | https://unpkg.com/leaflet@1.9.4/dist/leaflet.css | `a7837102824184820dfa198d1ebcd109ff6d0ff9a2672a074b9a1b4d147d04c6` |
| `LEAFLET-LICENSE.txt` | BSD-2-Clause | https://unpkg.com/leaflet@1.9.4/LICENSE | |

## Why Leaflet, not MapLibre

MapLibre GL needs WebGL. On the demo Mac, Chrome could not create a WebGL context, so
the map stayed blank. Leaflet draws with SVG, which works in every browser. Smooth color
changes come from CSS transitions on the SVG paths.

## Base map

Esri World Light Gray Canvas raster tiles, no key: `Base` under the data, `Reference`
(labels) above it so place names stay readable over the colored blocks.
Attribution: Esri, HERE, Garmin, © OpenStreetMap contributors.
CARTO raster tiles were tried first and now return an "API key required" watermark.
Offline, tiles fail quietly and the data still draws on a plain background.

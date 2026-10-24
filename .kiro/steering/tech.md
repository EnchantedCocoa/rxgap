---
inclusion: always
---
# Tech

- Python 3.11 venv at `../.venv` (uv). Run tools as `../.venv/bin/python ...`.
- Installed: osmnx, geopandas, shapely, scipy, requests, pytest. Add others with
  `uv pip install --python ../.venv/bin/python <pkg>` and say so.
- All distance and area math in Massachusetts State Plane, EPSG:26986 (meters).
- First line of every new source file: a one-line Korean comment stating its role.

## Commands
- Refresh pharmacies (Overpass, retries on 502): `../.venv/bin/python scripts/fetch_pharmacies.py`
- Block-group status: `../.venv/bin/python scripts/analyze_bg.py`
- Can't-afford-to-lose ranking: `../.venv/bin/python scripts/rank.py`
- Map: `../.venv/bin/python scripts/build_map.py` -> `map.html`
- Tests: `../.venv/bin/python -m pytest -q`

## Data facts (verified 2026-10-24)
- Block groups: all 580 Boston 2020 block groups from Census TIGER (`scripts/fetch_bg.py`).
  Not MassGIS EJ2020: that layer holds only environmental-justice block groups (462).
- Low-access compares each block group's no-car share to the STATE average (ACS), as HPC does.
- ACS 2022 5-year block-group query needs `CENSUS_KEY` in `.env` (never commit it).
  A missing/new key returns an HTML page, not JSON. 460 of 462 GEOIDs match.
- Pharmacies: OSM, 5 counties around Boston so stores across the city line count.
- Closed stores live in `data/manual/closures.csv` and are removed within 60 m.
- Overpass often returns 502. Always cache to `data/raw/` and never pull at load time.
- Boston OpenData MCP: `https://data-mcp.boston.gov/mcp` (City of Boston login).

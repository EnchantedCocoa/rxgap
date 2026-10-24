---
inclusion: always
---
# Structure

- `data/raw/` cached downloads (block groups, ACS, pharmacies, neighborhoods). Re-creatable.
- `data/manual/` hand-made inputs: `closures.csv`, later `officials.csv`, `candidate_sites.csv`.
- `data/` top level: analysis outputs (`bg_out.geojson`, `cant_lose.json`, `map_meta.json`).
- `scripts/` one script per step. Shared logic lives in `scripts/analyze_bg.py`.
- `tests/` pytest. Number checks go here.
- `docs/KIRO_LOG.md` running log of how Kiro was used (spec, hooks, MCP, Crew). The
  submission is written from it, so append as you go.
- `.kiro/specs/rxgap/` the spec. Requirements first, then design, then tasks.

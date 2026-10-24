# Implementation Plan

Tasks marked **[P]** in the same phase are independent and can run in parallel.
Each task names the requirements it serves and its done check. Cut order if behind:
1.7 NPI, 6.3 Crew, 4.3 PuLP (keep 4.4 fallback), extra languages in 5.4, House/Senate in
1.4 (keep council). Never cut 3.3 or the provenance tasks.

## Phase 0 — Setup (done)

- [x] 0.1 Steering, MCP config, hooks, venv, git
- [x] 0.2 Requirements approved
- [x] 0.3 Design approved

## Phase 1 — Data (all [P], each caches to `data/raw/`)

- [x] 1.1 Block groups from MassGIS EJ2020 (462 rows) — _Req 1_
- [x] 1.2 ACS 2022 block-group no-car, poverty, 65+ (key works) — _Req 1_
- [x] 1.3 [P] Pharmacies: add `healthcare=pharmacy` tag, keep `addr:*` tags, save fetch time — _Req 1, 2.3, 12_
  - Done: `raw/pharmacies.json` has an address or "not in OSM" for each store; 10 known stores spot-checked
- [x] 1.4 [P] Districts: council via Boston OpenData MCP, House and Senate from MassGIS; hand-fill `manual/officials.csv` with `source_url` — _Req 4.1_
  - Done: every Boston block group falls in one council, House and Senate district
- [x] 1.5 [P] Candidate sites: MassGIS health centers, MBTA rapid transit, `manual/candidate_sites.csv` — _Req 5.1_
  - Done: `raw/sites.json` with name, kind, lat, lon
- [x] 1.6 [P] Walk graph: osmnx walk network for Boston + 1 mi, saved as `raw/walk.graphml` — _Req 3.3_
  - Done: loads in under 10 s; one test route returns a sane time
- [x] 1.7 [P] (cut first) NPI cross-check with rapidfuzz, `source` field per store — _Req 12_
- [x] 1.8 [P] Vendor MapLibre GL JS + CSS into `app/vendor/`; pick and save base map style — _UI_
- [x] 1.9 Write `data/provenance.json` entries for every raw file (dataset, URL, pull date) — _Req 12_

## Phase 2 — Core analysis

- [x] 2.1 Coverage and status per block group (`analyze_bg.py`) — _Req 1_
- [x] 2.2 Per-store impact ranking (`rank.py`) + sum test — _Req 2_
- [ ] 2.3 Unit tests for `status_at` on synthetic squares — _Req 1_
- [ ] 2.4 Add address, districts to each store and lost block group (`route.py`) — _Req 2.3, 4.1_
- [ ] 2.5 [P] Three nearest remaining stores with walk minutes per lost block group (`walk.py`) — _Req 3.3_
- [ ] 2.6 [P] Simulation test: for top 3 stores, precomputed lost set = full rerun with that store closed — _Req 3_
- [ ] 2.7 `python -m rxgap.check`: rerun, diff against `data/last_status.json`, print changes — _Req 10_
- [ ] 2.8 [P] `scripts/verify_numbers.py` recomputes headline from `data/raw/` only — _Req 11_
- [ ] 2.9 [P] Validation text: write the Globe gap explanation first, then read the Globe's method and fill the comparison — _Req 9_

## Phase 3 — App: map and closure (biggest block)

- [ ] 3.1 `app/tokens.css` (colors, type, spacing, motion) and page layout: top bar, left panel, map — _UI_
- [ ] 3.2 Map layers: blocks with status color + pattern, store dots sized by rank, legend with source label — _Req 1, UI_
- [ ] 3.3 Closure moment: gray store, red wave, camera fit, results card, Undo — _Req 3_
  - Done: closing the top store shows 24,080 people, matching `cant_lose.json`, under 1 s
- [ ] 3.4 Ranked list with hover-to-highlight and keyboard support — _Req 2.3_
- [ ] 3.5 Block bottom sheet: people, 65+, no car, limited English, 3 nearest with walk times — _Req 3.2, 3.3_
- [ ] 3.6 "How we got this" (i) popovers on every number — _Req 12_
- [ ] 3.7 Banner when the income fallback rule is in use — _Req 1.2_
- [ ] 3.8 Method page with HPC rule and Globe comparison — _Req 9_
- [ ] 3.9 UI smoke test in a headless browser (close top store, check card number) — _Req 3, 8_

## Phase 4 — Siting and letter-count server

- [ ] 4.1 `rxgap/serve.py`: serves `app/`, `POST /count`, `GET /counts`, DuckDB, 127.0.0.1 only — _Req 7_
- [ ] 4.2 Siting gain per candidate by rerunning `status_at` on lost block groups (`site.py`) — _Req 5.1, 5.2_
- [ ] 4.3 PuLP max-coverage for best set of up to 3 — _Req 5.1_
- [ ] 4.4 Fallback: nearest health center with the same gain math — _Req 5.3_
- [ ] 4.5 Siting view: numbered pins, walk ring, restored blocks, before/after table — _Req 5.2_

## Phase 5 — Briefs and letters

- [ ] 5.1 Digit-free templates: `brief.en`, `letter.en`, `letter.es`, `letter.ht` + test that templates contain no digits — _Req 8_
- [ ] 5.2 `render(template, facts)` and facts builder from `cant_lose.json` / `sites.json` — _Req 8_
- [ ] 5.3 Brief page per official with print stylesheet and folium mini-map — _Req 4.2, 4.3_
- [ ] 5.4 Letter flow: address → Census geocoder → confirm officials → language + own sentence → letter + English copy, Copy and mailto, no send — _Req 6_
  - Extra languages (pt, zh, vi) only if time allows
- [ ] 5.5 Integrity test: every number in every rendered brief and letter is in the facts, and facts match analysis output — _Req 8_

## Phase 6 — Crew, write-up, video

- [ ] 6.1 Hook check: closure row added → pipeline reruns → map updates — _Req 3.1_
- [ ] 6.2 Run all tests and `verify_numbers.py`; fix any drift — _Req 8, 11_
- [ ] 6.3 (cut second) Crew daily 7:00 job running `rxgap.check`, posts to Slack only on change; trigger by hand for the demo — _Req 10_
- [ ] 6.4 Write the submission from `docs/KIRO_LOG.md`
- [ ] 6.5 Record the 3-minute demo

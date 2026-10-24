# Kiro log

How Kiro was used to build RxGap. Append as you go; the submission is written from this.

## 2026-10-24

- 11:04 Kiro set up a Python 3.11 venv and ran a first osmnx query: 46 pharmacies in the
  Boston city line.
- 11:19 Kiro tried a 5-county grid model. Rejected: a flat 1-mile grid flagged
  most of the inner city, and keyless Census data couldn't separate urban from suburban.
- 11:42 Switched to the state's method (HPC DataPoints 31) on MassGIS block groups.
  First check: the south half of Boston is thin (Roxbury, Hyde Park, Mattapan, Dorchester).
- 11:45 Removed the closed Codman Square Walgreens (585 Washington St). The desert
  population grew by about 25,000 under the stand-in rule. Built `map.html` with a
  walk-limit slider.
- 11:59 Census key added. The state low-access rule (cars + poverty) now applies:
  132,087 people in deserts, 158,214 in near-deserts.
- 12:05 Ranked stores by harm if closed. 19 stores carry every near-desert resident;
  the top CVS (Dorchester/Roxbury) alone holds 24,080. Test added: the ranking sums to
  the near-desert total exactly.
- 12:10 Phase 0: steering (product, tech, structure), Boston OpenData MCP config, two
  hooks (recompute on closure, number check on save), draft requirements spec.
- 12:15 Spec approved. Kiro wrote `design.md`: precomputed per-store impact powers both
  the ranking and the closure simulation (one source of truth, instant redraw); text from
  digit-free templates, numbers from a facts dict; letter counts in DuckDB on a
  localhost-only server.
- 12:18 Design updated for polish: MapLibre GL instead of Leaflet, one tokens file,
  an animated closure moment, print-ready brief, 3-step phone-first letter flow.
  Census key re-checked: 681 Suffolk block groups returned.
- 12:20 Design approved. Kiro wrote `tasks.md`: 6 phases, parallel tasks marked [P],
  each tied to requirements with a done check; cut order written at the top.
- 12:23 Phase 1 ran as 6 parallel Kiro Crew subagents (pharmacies, districts + officials,
  candidate sites, walk graph, NPI, MapLibre vendor). All 6 succeeded in about 4 minutes.
  Every block group now has a council, House and Senate district; 38 officials listed.
- 12:28 Found that all Rite Aid stores closed by Oct 2025, but OSM still lists 4 nearby.
  Added them to closures.csv. The East Boston one was #5 on the can't-lose list; removing
  it moved 10,856 people into deserts (desert total now 142,943).
- NPI cross-check: about 41 Boston retail pharmacies in NPI look missing from OSM, mostly
  in Dorchester and Roxbury. Not added yet; needs checking.
- 12:45 Phase 2. Each can't-lose store now carries, per lost block group: 65+, no-car,
  limited English, council/House/Senate district, and the 3 nearest remaining stores
  with walking minutes from the cached osmnx graph (top CVS: next store 25 min walk).
  `python -m rxgap.check` tested live: closing the top CVS flagged 30 block groups,
  undo restored them. `verify_numbers.py` matches the screen. Found and fixed: the
  pipeline re-pulled ACS every run (now cache-first) and wrote NaN into JSON.
  Globe gap text written before comparing: the Globe counted half-mile + mostly no car;
  the state rule is area-share and halves the limit for poverty too. 11 tests pass.
- 13:05 Phase 3: MapLibre app in `app/` (tokens.css holds every color). Closure moment:
  store grays out, its block groups fade to red in a wave outward, camera fits, a results
  card counts up to the code-made numbers and lists the officials. Every number has a
  "how we got this" popover. Local server serves only `app/` and `data/` on 127.0.0.1.
  Kiro drove a headless Chromium (Playwright) to close the #1 CVS and check the card reads
  24,080, matching `cant_lose.json`; it also caught two layout bugs from screenshots
  (Undo scrolled out of view, card covering the legend). 14 tests pass.
- 13:20 Bug from the user: the map stayed blank in their Chrome. Kiro reproduced it by
  driving real Chrome with Playwright: "Could not create a WebGL context". Switched the
  map from MapLibre GL (WebGL) to Leaflet (SVG), kept every interaction, moved map colors
  into CSS classes. CARTO tiles now show an "API key required" watermark, so the base map
  is Esri Light Gray. UI test now runs in real Chrome and checks all 462 blocks draw.
- 13:40 Phase 4. `scripts/siting.py` scores 198 candidate sites (52 health centers, 146 T
  stations, manual storefronts) per can't-lose store by how many cut-off residents they
  bring back above the 15% line, then PuLP (CBC) picks the best set of 3. Top CVS: best
  single site Whittier Street Health Center +14,588; best 3 together +21,722 of 24,080.
  Hyde Park Walgreens (#4): no listed site helps; the app says so. Map shows numbered
  sites, the walk ring, restored blocks turning green, and a before/after table.
  `rxgap.serve` now keeps letter counts in DuckDB (district + day only). Bugs caught by
  tests: a script named `site.py` shadowed Python's stdlib `site`; NaN in JSON broke the
  page (new strict-JSON test). 25 tests pass.
- 13:10 Asked about announced closures: none found for Boston (Walgreens named no MA
  closures for 2026). Kiro found the opposite gap instead: two Nubian Square pharmacies
  missing from OSM (new CVS at 32 Warren St, opened 2026-10-07; Kornfield Pharmacy).
  Added `data/manual/openings.csv` (each row has a source URL). Desert population
  142,943 -> 121,319; 24 block groups changed. Sullivan's (Roslindale) is now #1;
  the Blue Hill Ave CVS drops to #2 (20,083). Kornfield itself enters the list at #12.
- 13:25 User asked to toggle to other MA places. Kiro pulled the HPC's own public
  block-group dataset (DataPoints 31) and joined it to towns via Census TIGER. Most
  at-risk city: Springfield (52,513 in desert or near-desert, 34%). Most affected
  suburban town: Plymouth (21,966, 36%, 97% suburban block groups).
  Two problems found by comparing with HPC: (1) the MassGIS EJ2020 layer only holds
  EJ block groups, so our Boston map has 462 of 580 block groups (571k of 676k people);
  (2) our Boston desert count (121,319) is ~4x HPC's (31,291), mainly because OSM lists
  far fewer pharmacies than the state license data HPC used.

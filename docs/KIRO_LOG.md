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
- 13:45 Fixes from the HPC comparison. (1) Low-access now compares no-car share to the
  STATE average (11.9%, ACS), as the HPC does; we had used Boston's (~33%). Checked on
  HPC's own block data: the state-average rule matches 97% of their low-access flags.
  (2) Block groups now come from Census TIGER: all 580 Boston block groups (675,647
  people), not the 462 EJ-only MassGIS layer. Result: desert 173,050, near-desert
  188,091; 24 can't-lose stores. A test caught one 7-person block that depends on three
  stores at once; the test was too strict and now counts each block group once.
- 14:00 Store list fix. Pulled NPI retail pharmacies (Boston + neighboring ZIPs), kept
  only Community/Retail with no institutional/mail/specialty codes, geocoded with the
  Census geocoder, matched to OSM. 75 NPI-only addresses would change a Boston block;
  4 parallel Kiro Crew subagents checked each one on the web (store pages, news):
  58 open, 13 closed, 4 unclear. Kiro re-checked the Gallivan Blvd Walgreens (a helper
  said open; the Globe says it closed 2025-04-28) and dropped 533 Columbia Rd (not on
  the Walgreens locator). 54 confirmed-open stores added to openings.csv with evidence
  URLs, mostly health-center and grocery pharmacies OSM was missing.
  Result: desert 173,050 -> 42,417; near-desert 89,889. Versus the HPC's own block
  data (June 2025): same status for 86% of residents. New test keeps it >= 80%.
- 14:10 Town picker. Springfield (most at-risk large city: 29,506 desert + 23,007
  near-desert) and Plymouth (most at-risk mostly-suburban town: 14,015 + 7,951) show the
  HPC's own block-group results, with each block's area type (urban 1 mi / suburban
  2 mi, halved for low-access). Closure simulation stays Boston-only until those towns
  get a checked store list. UI test switches towns and checks the headline numbers.
- 14:15 Demo review fixes. Landing view opens on Dorchester/Mattapan/Roxbury at zoom 13,
  covered blocks are fainter so red/amber stand out, and a code-made line reads "20% of
  Boston residents live in a desert or one closure away". Blocks under 50 residents
  (parks, harbor islands) are gray. Method page now shows the state's 31,291 and our
  86% agreement. A replacement site next to the closed store is labeled as such.
- 14:20 Headline reframed after user feedback that "543,341 covered" made deserts look
  trivial. The big number is now people in a desert or one closure away (132,306, "1 in 5",
  19,996 age 65+, 14,258 homes with no car); the covered count is gone from the headline
  and the bar's remainder is neutral gray. All figures still come from app_data.json.
- 14:35 Two visual upgrades. (1) Closure moment now draws the real street route (cached
  osmnx walk graph, `scripts/routes.py`) from the hardest-hit block to the next open
  pharmacy, with a "35 min walk" tag; a test checks the tag equals the analysis minutes.
  (2) A 5-stop opening tour (skippable, ends on any click, off under reduced motion) whose
  captions are fixed templates filled with app_data.json numbers. Store names from NPI are
  shown in display form ("CVS Pharmacy", not "CVS PHARMACY #05464"). 29 tests pass.
- 15:20 Springfield and Plymouth are now full places (same pipeline as Boston), via
  `scripts/places.py` + `RXGAP_PLACE` and `scripts/run_all.py`. Each block group now gets
  the HPC area type from its density (urban 1 mi / suburban 2 mi / rural 5 mi, halved
  for low-access), in Boston too. Overpass refused connections all afternoon, so
  Springfield's store list is NPI-only and both new towns use straight-line x 1.3 walk
  estimates (labeled). 7 parallel subagent checks verified 124 pharmacy addresses.
  Found and fixed a de-duplication bug: two different brands within 60-120 m (e.g.
  Stop & Shop next to Walgreens on Samoset St) were counted as one store; now same
  store = close AND same brand. Agreement with the HPC by residents: Boston 88%,
  Plymouth 79%, Springfield 73% (HPC excluded some provider-based pharmacies we count).
- 15:55 Opening photo essay (`app/essay.js`, `app/essay.css`). Two parallel subagents: one found
  free-licensed photos (Wikimedia Commons / Flickr CC, credits in `data/manual/photos.json`),
  one verified health-impact facts against primary sources (`data/manual/evidence.json`,
  12 facts, each with URL and verbatim quote; rejected the weakly sourced "125,000 deaths").
  No digits in the story text: outside facts render from evidence.json with a source link,
  our numbers from app_data.json with the "i" provenance button. No free-licensed photo of a
  pharmacy-closure protest exists, so none is shown. Test checks every number's origin.

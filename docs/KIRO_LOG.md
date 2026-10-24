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

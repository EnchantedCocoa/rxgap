# Checklist

## Phase 0 · Setup
- [x] Steering: product, tech, structure
- [x] Boston OpenData MCP in .kiro/settings/mcp.json (needs City of Boston login on connect)
- [x] Hooks: recompute on closure, number check on save
- [x] Draft requirements spec
- [ ] User approves requirements, then design.md, then tasks.md
- [ ] Connect the MCP in Kiro and run one query (log it)

## Phase 1 · Data
- [x] Pharmacies (OSM, 5 counties, cached)
- [x] Block groups (MassGIS EJ2020)
- [x] ACS 2022: no-car, poverty, 65+
- [x] Neighborhood names
- [x] closures.csv seeded (Codman Square)
- [ ] Check OSM against 10 known stores; Morton St and Gallivan Blvd confirmed absent
- [ ] Store addresses for the ranking
- [ ] Council districts (via MCP), state House/Senate districts
- [ ] officials.csv
- [ ] Candidate sites: health centers, MBTA stations, candidate_sites.csv
- [ ] Cached osmnx walking graph for Boston
- [ ] Optional: NPI cross-check

## Phase 2 · Analysis
- [x] Coverage + status per block group
- [x] Can't-afford-to-lose ranking + sum test
- [ ] Validation line vs Globe ~15,000 (write the gap paragraph first)
- [ ] rxgap.check CLI, verify_numbers.py

## Phase 3-5
- [ ] Map + closure simulation screen
- [ ] Brief, siting, letters, number-integrity test
- [ ] Crew daily job, write-up, video

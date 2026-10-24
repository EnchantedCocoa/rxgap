# RxGap plan

Pitch: when a neighborhood's pharmacy closes, people stop taking their heart medicine.
RxGap shows each affected neighborhood's officials who just lost access and where a
replacement would help most, and helps residents write to their own representatives.

Four screens: risk map, closure simulation, official's brief, resident letter.
Full requirements: `.kiro/specs/rxgap/requirements.md`. Method and rules: `.kiro/steering/`.

| Phase | Done when |
|---|---|
| 0 Setup | Steering, MCP, hooks, spec drafted; spec approved |
| 1 Data | Pharmacies, block groups, ACS, districts, candidate sites cached in data/raw/ |
| 2 Analysis | Coverage, near-desert, ranking, validation line pass tests |
| 3 Screens 1-2 | Closing a store redraws the map in seconds |
| 4 Brief, siting, letters | Brief + Haitian Creole letter with code-inserted numbers |
| 5 Crew, write-up, video | Slack post fires; submission written from docs/KIRO_LOG.md |

Cut order if behind: NPI cross-check, Crew, siting optimizer (use nearest health
center), extra languages (keep Spanish + Haitian Creole), state districts (keep council).
Never cut: closure simulation, "how we got this" links.

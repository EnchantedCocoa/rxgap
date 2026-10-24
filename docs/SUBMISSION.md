# RxGap: when a pharmacy closes, who loses access?

**Hackachusetts challenge:** Civic action: V2 (who an alert misses) and community readiness

**Repo:** https://github.com/EnchantedCocoa/rxgap · **Try it:** clone, then `python -m rxgap.serve` and open the local address it prints.

## Inspiration

When a neighborhood pharmacy closes, older adults stop filling their heart medicine, and the drop lasts a year (Qato et al., JAMA Network Open, 2019). The people hit hardest are the ones a closure alert is least likely to reach: older adults, homes without a car, and neighbors who speak limited English. Massachusetts already has 580,000 people in pharmacy deserts (Massachusetts Health Policy Commission, 2025), and the big chains are closing stores. We wanted a tool that turns "a store is closing" into "these blocks, these people, these officials, and this is the fix."

## What it does

RxGap uses the state's own method (DataPoints 31, October 2025) on census block groups, for Boston, Springfield and Plymouth.

- **Risk map.** Every block group is a pharmacy desert, one closure away, or covered.
- **Stores a place can't afford to lose.** Stores ranked by how many residents would land in a desert if each one closed.
- **Closure simulation.** Close any store: the lost blocks turn red, the street route to the next open pharmacy appears, and a card shows the residents, older adults, homes without a car and limited-English homes affected.
- **Best replacement site.** Health centers, transit stops and other sites ranked by how many cut-off residents they bring back. An optimizer picks the best set.
- **Officials.** A one-page, printable brief for each affected council member and state legislator, with the blocks in their district and the best sites.
- **Get medicine delivered.** Store delivery, plan mail order, refills synced to one day, and vaccine rides, in 3 languages. It has no input fields and keeps no data.
- **Write a letter.** Enter an address (or click your block), confirm your officials, add your own words, and get a letter in English, Spanish or Haitian Creole with an English copy. One topic asks officials to keep a pharmacy near you. The other asks MassHealth to pay for pharmacy rides or delivery, because today it does not pay for rides to pick up medicine (130 CMR 407.411(B)(9)).
- **Daily check.** A Kiro Crew job reruns everything each morning and speaks up only when a block group changes status.

### What RxGap finds

| Place | In a desert | One closure away | Share of residents at risk | Same status as the state | Store it can least afford to lose |
|---|---|---|---|---|---|
| Boston | 39,549 | 78,693 | 1 in 6 | 88% | CVS Pharmacy, 1575 Blue Hill Ave: 12,623 residents |
| Springfield | 18,675 | 33,158 | 1 in 3 | 73% | Baystate Pharmacy - Mason Square, 11 Wilbraham Rd: 8,544 residents |
| Plymouth | 16,198 | 12,986 | 1 in 2 | 79% | CVS Pharmacy, 517 State Road: 6,614 residents |

## How we built it with Kiro

- **Spec first.** Kiro wrote the requirements, then the design, then a task plan with parallel tasks marked and a cut order at the top (`.kiro/specs/rxgap/`). Two features came from research mid-build and went into the spec before any code: the delivery helper and the MassHealth letter.
- **Steering.** Three steering files hold the method, the data facts and the rules ("every number in a letter is inserted by code", "never send for a resident", "every number has a how-we-got-this link").
- **Hooks.** "Recompute on closure" reruns the whole pipeline when the store list changes and reports which block groups moved. "Number check on save" runs the integrity tests when analysis or template code changes.
- **MCP.** Boston's OpenData MCP server for the council districts.
- **Kiro Crew subagents for parallel work.** 6 subagents pulled the first data sets at once. 4 subagents checked 75 pharmacies on the web that the federal NPI list had but OpenStreetMap did not, and 54 confirmed-open stores were added, each with a source. 7 more verified 124 store addresses for Springfield and Plymouth. 2 found free-licensed photos and checked every health fact in the story against its primary source.
- **Kiro Crew schedule.** The daily check is a zero-token script job at seven in the morning that notifies only on change.
- **Real-browser testing.** Kiro drove real Chrome with Playwright to close stores, read the numbers on the card and compare them with the analysis files. That is how it caught a blank map (no WebGL on the demo laptop), which made us switch the map from MapLibre to Leaflet.

## Number integrity

Nothing a resident or official reads contains a hand-typed number. The brief, letter and helper templates have no digits. Code fills every number from `facts.json`, which is built from the analysis output. One renderer exists in Python and in JavaScript, and a test makes sure both write the same text. Tests also check that every number printed came from a fact and that every fact matches the analysis. This write-up follows the same rule: `scripts/build_submission.py` fills it from the data.

## Challenges we ran into

- **OpenStreetMap undercounts pharmacies.** Our first desert count was far above the state's. We cross-checked the federal NPI list, verified every candidate on the web, and added only confirmed-open stores with a source.
- **The wrong block-group layer.** A state layer we started with holds only environmental-justice block groups (462 in Boston). We moved to all 580 Census TIGER block groups.
- **Closures OSM still lists.** Every Rite Aid in the state has closed. A hand-kept closures list with sources removes them.
- **Overpass outages.** For two towns the walking graph was unavailable, so walk times there are straight-line estimates, labeled on screen.
- **The obvious fix did not exist.** We planned to help residents request MassHealth rides to the pharmacy. The regulation says MassHealth does not pay for them, so we built delivery help and a letter asking MassHealth to change that instead.

## What we're proud of

- The closure moment: one click shows exactly who loses access and who represents them.
- Agreement with the state's own block-group results without tuning the method to match.
- A letter flow in three languages that keeps no personal data and never sends anything.

## What's next

- A native-speaker review of the Spanish and Haitian Creole text.
- More towns, and the NPI cross-check for Springfield.
- A map export for Boston's proposed Pharmacy Stabilization and Access Fund, which asks the city to identify areas of limited pharmacy access.
- Support for the push to lengthen closure notice from 14 days to 120 days.

---
*RxGap is an AI tool built at Hackachusetts. It is not the City of Boston or any government office.*

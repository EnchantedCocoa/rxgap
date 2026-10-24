# RxGap

**When a neighborhood's pharmacy closes, people stop taking their heart medicine.**

RxGap is a civic tool for Massachusetts. It shows which census block groups lose walkable pharmacy
access when a store closes, and who lives there (older adults, homes without a car, limited-English
households). It ranks the stores a place can't afford to lose and finds the best replacement sites.
It gives each affected official a one-page brief, and it helps residents get their medicine delivered
and write to their own representatives.

> RxGap is an AI tool built at Hackachusetts. It is not the City of Boston or any government office,
> and it never sends anything on a resident's behalf.

## What you can do in the app

| Screen | What it does |
|---|---|
| Story | A short photo essay on pharmacy closures, with sourced numbers |
| Risk map | Every block group as a pharmacy desert, one closure away, or covered |
| Stores you can't afford to lose | Stores ranked by how many residents would land in a desert if each one closed |
| Closure simulation | Close any store: the lost blocks turn red, with walking routes to the next pharmacy |
| Best replacement site | Health centers, transit stops and other sites ranked by residents they bring back |
| Officials | A one-page, printable brief for each council member and state legislator |
| Get medicine delivered | Delivery, mail order, synced refills and vaccine rides, in English, Spanish and Haitian Creole |
| Write a letter | Address → your officials → your own words → a letter you send yourself |

Places: **Boston**, **Springfield** (city) and **Plymouth** (suburban).

## Method

Massachusetts Health Policy Commission, *DataPoints 31* (October 2025), applied to 2020 census block groups:

- A block group is a **desert** when less than 15% of its area is within the walk limit of an open pharmacy.
- The walk limit is 1 mile in urban areas, 2 in suburban and 5 in rural, halved for low-access block
  groups (car ownership below the state average, or more than 20% of households in poverty).
- A **near-desert** is covered today but becomes a desert if one specific pharmacy closes.

We did not tune the method to match the state's or the Boston Globe's counts. The app's
"Method & sources" page explains the differences.

## Rules the code keeps

- **Every number on screen comes from data**, and has an "i" button or a source link that says how we got it.
- **Letters and briefs never contain a hand-typed number.** Templates in `data/templates/` hold no
  digits; code inserts every number from `facts.json`. Tests fail otherwise (`tests/test_text.py`).
- **Nothing is sent for you.** Letters are drafts with Copy, Print and "Open in my email".
- **Privacy.** An address goes to the US Census geocoder only to find the block. It is never stored or
  logged. Letter counts keep only the district.

## Run it

Python 3.11. The server binds to 127.0.0.1 only and has no login, so keep it on your own machine.

```sh
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chrome      # only for the UI tests

python -m rxgap.serve 8765               # then open http://127.0.0.1:8765/app/
python -m pytest -q                      # analysis, number-integrity and UI tests
```

URL options: `?splash=0` skips the story, and `?tour=0` skips the guided tour.

Rebuild everything from the cached data in `data/raw/`:

```sh
python scripts/run_all.py                # all places; or: python scripts/run_all.py boston
```

The ACS pull needs a free Census API key in `.env` as `CENSUS_KEY=...`. The cached files mean you do
not need one to run the app or the tests. The walking graph (`data/raw/walk.graphml`) is too large for
git. `scripts/fetch_walk_graph.py` rebuilds it from OpenStreetMap. Without it, walk times fall back to
straight line × 1.3, labeled as an estimate. The routes already computed live in `data/routes.json`.

## Layout

| Path | What is there |
|---|---|
| `app/` | The web app: `app.js` (map), `essay.js` (story), `act.js` (briefs, helper, letters), `text.js` (template renderer) |
| `rxgap/` | `serve.py` (local server, letter counts, geocoder proxy), `text.py` (the same renderer in Python), `check.py` |
| `scripts/` | One script per pipeline step; `run_all.py` runs them per place |
| `data/raw/` | Cached downloads; `data/manual/` hand-made inputs with sources |
| `data/` | Analysis outputs for Boston; `data/places/<place>/` for the others |
| `data/templates/` | Digit-free text for briefs, letters and the delivery helper |
| `tests/` | pytest, including real-Chrome UI tests |
| `.kiro/` | Kiro spec (requirements, design, tasks), steering and hooks |
| `docs/KIRO_LOG.md` | How Kiro was used, step by step |

## Data sources

- Pharmacies: © OpenStreetMap contributors (ODbL), plus stores added by hand with a source URL
  (`data/manual/openings.csv`) and closures (`data/manual/closures.csv`); NPI registry cross-check.
- Block groups and demographics: US Census Bureau TIGER/Line 2020 and ACS 2022 5-year.
- Districts: MassGIS (state House and Senate), City of Boston (council). Officials: `data/manual/officials.csv`.
- Candidate sites: MassGIS community health centers, MBTA stations.
- Pharmacy deserts: Massachusetts Health Policy Commission public block-group dataset.
- Rules for the delivery helper and letters: `data/manual/policy.json`, each with a link and the date we checked it.
- Story facts: `data/manual/evidence.json`, each with a link.
- Base map: Esri, HERE, Garmin, © OpenStreetMap contributors.

## Photo credits

| Photo | By | License |
|---|---|---|
| Closed Walgreens, Oakland | Mx. Granger (Wikimedia Commons) | CC0 1.0 |
| Empty Rite Aid, Los Angeles | Downtowngal (Wikimedia Commons) | CC BY-SA 4.0 |
| Closed Rite Aid, Waterford, CT | jjbers (Flickr) | CC BY 2.0 |
| Mattapan Square, Boston | 4300streetcar (Wikimedia Commons) | CC BY 4.0 |
| Pharmacy access rally | Pharmacists United for Truth and Transparency (PUTT) | Courtesy photo |

Full captions and source links: `data/manual/photos.json`.

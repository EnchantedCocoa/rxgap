# 보스턴 시의회/주 하원/주 상원 선거구를 받아 캐시하고 블록그룹 커버리지를 검증하는 스크립트.
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings('ignore')
import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
MANUAL = ROOT / 'data' / 'manual'

# --- source definitions -----------------------------------------------------
COUNCIL_URL = (
    'https://data.boston.gov/dataset/3e632d04-d7fe-4acd-bab7-75be4bdcfa96/'
    'resource/2d9092dd-5175-49ab-9b18-0c0efcef4153/download/'
    'city_council_districts___2023_2032.geojson'
)
COUNCIL_DATASET = 'City Council Districts - 2023-2032 (Analyze Boston / data.boston.gov)'

HOUSE_SVC = ('https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/'
             'AGOL/House2021/FeatureServer/1')
SENATE_SVC = ('https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/'
              'AGOL/Senate2021/FeatureServer/1')
HOUSE_DATASET = 'MassGIS Massachusetts House Legislative Districts (2021) polygons layer'
SENATE_DATASET = 'MassGIS Massachusetts Senate Legislative Districts (2021) polygons layer'

HEADERS = {'User-Agent': 'rxgap/1.0 (pharmacy-desert hackathon tool)'}


def _now():
    return datetime.now(timezone.utc).isoformat()


def get_json(url, params=None, tries=5):
    """GET with exponential backoff; returns parsed JSON."""
    delay = 3
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            print(f'  retry {i + 1}/{tries} after {delay}s ({str(e)[:120]})', file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f'failed to fetch {url}: {last}')


def fetch_council():
    """Boston City Council districts GeoJSON (already EPSG:4326)."""
    gj = get_json(COUNCIL_URL)
    out = RAW / 'council.geojson'
    out.write_text(json.dumps(gj))
    print(f'council: {len(gj["features"])} features -> {out}')
    return COUNCIL_DATASET, COUNCIL_URL


def fetch_arcgis_polygons(svc, out_name, dataset):
    """Query every polygon from an ArcGIS FeatureServer layer as GeoJSON (EPSG:4326)."""
    params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true',
              'outSR': '4326', 'f': 'geojson'}
    gj = get_json(svc + '/query', params=params)
    feats = gj.get('features', [])
    out = RAW / out_name
    out.write_text(json.dumps(gj))
    print(f'{out_name}: {len(feats)} features -> {out}')
    return dataset, svc + '/query'


# --- district id / name extraction ------------------------------------------
def council_id(props):
    return str(int(props['DISTRICT']))


def council_name(props):
    return props.get('LONGNAME') or f"District {council_id(props)}"


def house_id(props):
    return str(props.get('REP_DIST') or '').strip()


def house_name(props):
    return house_id(props)


def senate_id(props):
    return str(props.get('SEN_DIST') or '').strip()


def senate_name(props):
    return senate_id(props)


def _clean_person(raw):
    """'Judith A. Garcia\xa0(D)' -> 'Judith A. Garcia'."""
    if not raw:
        return ''
    s = str(raw).replace('\xa0', ' ')
    if '(' in s:
        s = s.split('(')[0]
    return s.strip().rstrip(',').strip()


# --- coverage verification ---------------------------------------------------
def assign_by_area(bg, districts, id_fn, label):
    """For each block group, the district id holding the largest share of its area.

    A block group that overlaps no district (e.g. a non-Boston edge block group
    vs. the city-only council layer) falls back to the NEAREST district, logged
    explicitly so the assignment is never silently wrong.

    Returns (assignment dict GEOID->id, n_assigned, n_split_gt10pct, n_fallback).
    Areas and distances computed in EPSG:26986 (MA state plane, meters).
    """
    bg_m = bg.to_crs(26986)
    d_m = districts.to_crs(26986)
    d_geoms = list(d_m.geometry)
    d_ids = [id_fn(r) for r in d_m.to_dict('records')]

    sidx = d_m.sindex
    assignment = {}
    n_split = 0
    n_fallback = 0
    for _, row in bg_m.iterrows():
        g = row.geometry
        a = g.area
        if a <= 0:
            continue
        cand = list(sidx.query(g, predicate='intersects'))
        shares = []
        for j in cand:
            inter = g.intersection(d_geoms[j])
            if not inter.is_empty:
                shares.append((d_ids[j], inter.area / a))
        if not shares:
            # no overlap: assign nearest district boundary, and log it
            dists = [(d_ids[j], g.distance(d_geoms[j])) for j in range(len(d_geoms))]
            nid, ndist = min(dists, key=lambda x: x[1])
            assignment[row['GEOID']] = nid
            n_fallback += 1
            print(f'  {label} fallback: bg {row["GEOID"]} has no overlap, '
                  f'assigned nearest district {nid} ({ndist:.0f} m away)')
            continue
        shares.sort(key=lambda x: x[1], reverse=True)
        assignment[row['GEOID']] = shares[0][0]
        # split by >10%: at least one *other* district holds >10% of this bg
        if any(s > 0.10 for _, s in shares[1:]):
            n_split += 1
    print(f'{label}: {len(assignment)}/{len(bg_m)} block groups assigned '
          f'({n_fallback} by nearest-district fallback); '
          f'{n_split} split across >1 district by >10% area')
    return assignment, len(assignment), n_split, n_fallback


def boston_district_ids(assignment):
    """Set of district ids that hold the plurality of at least one Boston block group."""
    return sorted(set(assignment.values()))


# --- officials.csv -----------------------------------------------------------
# Current Boston City Council as of October 2026 (source: boston.gov city council page).
COUNCIL_OFFICIALS = {
    '1': ('Gabriela Coletta Zapata', 'https://www.boston.gov/departments/city-council/gabriela-coletta'),
    '2': ('Edward M. Flynn', 'https://www.boston.gov/departments/city-council/ed-flynn'),
    '3': ('John FitzGerald', 'https://www.boston.gov/departments/city-council/john-fitzgerald'),
    '4': ('Brian Worrell', 'https://www.boston.gov/departments/city-council/brian-worrell'),
    '5': ('Enrique J. Pepén', 'https://www.boston.gov/departments/city-council/enrique-pepen'),
    '6': ('Benjamin J. Weber', 'https://www.boston.gov/departments/city-council/benjamin-weber'),
    '7': ('Miniard Culpepper', 'https://www.boston.gov/departments/city-council/miniard-culpepper'),
    '8': ('Sharon Durkan', 'https://www.boston.gov/departments/city-council/sharon-durkan'),
    '9': ('Liz Breadon', 'https://www.boston.gov/departments/city-council/liz-breadon'),
}
COUNCIL_AT_LARGE = [
    ('Ruthzee Louijeune', 'https://www.boston.gov/departments/city-council/ruthzee-louijeune'),
    ('Julia M. Mejia', 'https://www.boston.gov/departments/city-council/julia-mejia'),
    ('Erin J. Murphy', 'https://www.boston.gov/departments/city-council/erin-murphy'),
    ('Henry Santana', 'https://www.boston.gov/departments/city-council/henry-santana'),
]
COUNCIL_OFFICE = '1 City Hall Square, Room 550, Boston, MA 02201'
COUNCIL_EMAIL_FMT = ''  # per-councilor emails vary; left blank unless on the official page

HOUSE_OFFICE = 'Massachusetts State House, 24 Beacon St., Boston, MA 02133'
SENATE_OFFICE = 'Massachusetts State House, 24 Beacon St., Boston, MA 02133'


def build_officials(council_gdf, house_gdf, senate_gdf, house_ids, senate_ids):
    """Write data/manual/officials.csv. Returns (filled, unverified)."""
    import csv
    rows = []
    filled = unverified = 0

    def add(dtype, did, name, email, office, src):
        nonlocal filled, unverified
        if name:
            filled += 1
        else:
            unverified += 1
            src = 'UNVERIFIED'
        rows.append([dtype, did, name, email, office, src])

    # council districts (ids come straight from the geojson)
    gj_ids = {council_id(r) for r in council_gdf.to_dict('records')}
    for did in sorted(gj_ids, key=lambda x: int(x)):
        name, src = COUNCIL_OFFICIALS.get(did, ('', ''))
        add('council', did, name, '', COUNCIL_OFFICE, src)
    # at-large (4)
    for name, src in COUNCIL_AT_LARGE:
        add('council_at_large', 'at-large', name, '', COUNCIL_OFFICE, src)

    # house: current rep + official URL embedded in the MassGIS layer
    h = {house_id(r): r for r in house_gdf.to_dict('records')}
    for did in house_ids:
        r = h.get(did, {})
        name = _clean_person(r.get('REP'))
        url = (r.get('URL') or '').strip()
        add('house', did, name, '', HOUSE_OFFICE,
            url or 'https://malegislature.gov/Legislators/Members/House')

    # senate
    s = {senate_id(r): r for r in senate_gdf.to_dict('records')}
    for did in senate_ids:
        r = s.get(did, {})
        name = _clean_person(r.get('SENATOR'))
        url = (r.get('URL') or '').strip()
        add('senate', did, name, '', SENATE_OFFICE,
            url or 'https://malegislature.gov/Legislators/Members/Senate')

    MANUAL.mkdir(parents=True, exist_ok=True)
    out = MANUAL / 'officials.csv'
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['district_type', 'district_id', 'name', 'email', 'office_address', 'source_url'])
        w.writerows(rows)
    print(f'officials.csv: {len(rows)} rows ({filled} filled, {unverified} unverified) -> {out}')
    return filled, unverified


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    meta = {}
    ds, url = fetch_council()
    meta['council'] = {'dataset': ds, 'url': url, 'pulled': _now()}
    ds, url = fetch_arcgis_polygons(HOUSE_SVC, 'house.geojson', HOUSE_DATASET)
    meta['house'] = {'dataset': ds, 'url': url, 'pulled': _now()}
    ds, url = fetch_arcgis_polygons(SENATE_SVC, 'senate.geojson', SENATE_DATASET)
    meta['senate'] = {'dataset': ds, 'url': url, 'pulled': _now()}
    meta['function'] = 'scripts/fetch_districts.py:main'
    (RAW / 'districts.meta.json').write_text(json.dumps(meta, indent=2))
    print(f'wrote {RAW / "districts.meta.json"}')

    # --- coverage check ---
    bg = gpd.read_file(RAW / 'boston_bg.geojson')
    council = gpd.read_file(RAW / 'council.geojson')
    house = gpd.read_file(RAW / 'house.geojson')
    senate = gpd.read_file(RAW / 'senate.geojson')

    c_assign, c_n, c_split, c_fb = assign_by_area(bg, council, lambda r: council_id(r), 'council')
    h_assign, h_n, h_split, h_fb = assign_by_area(bg, house, lambda r: house_id(r), 'house')
    s_assign, s_n, s_split, s_fb = assign_by_area(bg, senate, lambda r: senate_id(r), 'senate')

    # districts touching Boston = those assigned as plurality to >=1 block group
    house_ids = boston_district_ids(h_assign)
    senate_ids = boston_district_ids(s_assign)
    print(f'boston-touching: {len(house_ids)} house, {len(senate_ids)} senate districts')

    filled, unverified = build_officials(council, house, senate, house_ids, senate_ids)

    print('\n=== SUMMARY ===')
    print(f'council: assigned {c_n}/{len(bg)} ({c_fb} nearest-fallback), split>10% {c_split}')
    print(f'house:   assigned {h_n}/{len(bg)} ({h_fb} nearest-fallback), split>10% {h_split}')
    print(f'senate:  assigned {s_n}/{len(bg)} ({s_fb} nearest-fallback), split>10% {s_split}')
    print(f'officials: {filled} filled, {unverified} unverified')
    return {'council': (c_n, c_split, c_fb), 'house': (h_n, h_split, h_fb),
            'senate': (s_n, s_split, s_fb),
            'house_ids': house_ids, 'senate_ids': senate_ids,
            'filled': filled, 'unverified': unverified}


if __name__ == '__main__':
    main()

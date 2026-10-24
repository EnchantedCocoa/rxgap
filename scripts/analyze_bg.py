# 폐점을 반영해 보스턴 블록그룹별 약국 사막 상태를 계산하는 스크립트.
import csv, json, os, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
import geopandas as gpd
import requests
from shapely.geometry import Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
MILE = 1609.344
RADII = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]  # miles, for the map slider
CLOSED_MATCH_M = 60


def census_key():
    if os.environ.get('CENSUS_KEY'):
        return os.environ['CENSUS_KEY'].strip()
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('CENSUS_KEY='):
                return line.split('=', 1)[1].strip()
    return ''


def fetch_acs(key):
    """Block-group no-car, poverty and 65+ counts for Suffolk County (Boston)."""
    age = [f'B01001_0{n:02d}E' for n in list(range(20, 26)) + list(range(44, 50))]
    vars_ = ['B25044_001E', 'B25044_003E', 'B25044_010E', 'B17017_001E', 'B17017_002E'] + age
    r = requests.get('https://api.census.gov/data/2022/acs/acs5',
                     params={'get': ','.join(vars_), 'for': 'block group:*',
                             'in': 'state:25 county:025', 'key': key}, timeout=60)
    rows = r.json()  # raises on the "Missing/Invalid Key" HTML page
    head, out = rows[0], {}
    for row in rows[1:]:
        d = dict(zip(head, row))
        geoid = d['state'] + d['county'] + d['tract'] + d['block group']
        n = lambda v: max(int(d[v] or 0), 0)
        out[geoid] = {'hh': n('B25044_001E'), 'nocar': n('B25044_003E') + n('B25044_010E'),
                      'pov_hh': n('B17017_001E'), 'pov': n('B17017_002E'),
                      'age65': sum(n(v) for v in age)}
    (DATA / 'raw' / 'acs_bg.json').write_text(json.dumps(out))
    return out


def load_pharmacies():
    phs = json.loads((DATA / 'raw' / 'pharmacies.json').read_text())['pharmacies']
    for p in phs:
        p['source'] = 'OpenStreetMap'
    # Stores OSM is missing (new or unmapped), each with a source URL. Skipped if OSM already has one within 60 m.
    opened = DATA / 'manual' / 'openings.csv'
    if opened.exists():
        with open(opened) as f:
            for row in csv.DictReader(f):
                o = Point(float(row['lon']), float(row['lat']))
                # degrees -> rough meters (longitude scale at 42°N)
                if not any(o.distance(Point(p['lon'], p['lat'])) * 82000 <= CLOSED_MATCH_M for p in phs):
                    phs.append({'name': row['name'], 'lat': float(row['lat']), 'lon': float(row['lon']),
                                'address': row['address'], 'source': 'manual (openings.csv)'})
                    print(f"opening '{row['name']}': added")
    ph = gpd.GeoDataFrame(phs, geometry=[Point(p['lon'], p['lat']) for p in phs], crs=4326).to_crs(26986)
    for c in ['name', 'address', 'osm_id', 'brand', 'source']:  # NaN -> None, so JSON stays valid
        if c in ph:
            ph[c] = ph[c].astype(object).where(ph[c].notna(), None)
    closed = []
    with open(DATA / 'manual' / 'closures.csv') as f:
        for row in csv.DictReader(f):
            closed.append(row)
    cl = gpd.GeoSeries([Point(float(c['lon']), float(c['lat'])) for c in closed], crs=4326).to_crs(26986)
    drop = set()
    for c, g in zip(closed, cl):
        hit = ph.index[ph.distance(g) <= CLOSED_MATCH_M]
        print(f"closure '{c['name']}': removed {len(hit)} OSM entry")
        drop |= set(hit)
    return ph.drop(index=list(drop)), closed


def status_at(geom, ph, r):
    near = ph[ph.distance(geom) <= r]
    if len(near) == 0:
        return 0.0, 'desert'
    share = geom.intersection(unary_union(list(near.geometry.buffer(r)))).area / geom.area
    if share < 0.15:
        return share, 'desert'
    for i in near.index:
        rest = near.drop(i)
        s = 0 if len(rest) == 0 else geom.intersection(unary_union(list(rest.geometry.buffer(r)))).area / geom.area
        if s < 0.15:
            return share, 'near-desert'
    return share, 'covered'


def prepare():
    """Block groups with low-access flag, walk radius, 65+/no-car counts and neighborhood."""
    bg = gpd.read_file(DATA / 'raw' / 'boston_bg.geojson').to_crs(26986)
    ph, closed = load_pharmacies()

    key = census_key()
    acs, rule = None, 'income'
    cached = DATA / 'raw' / 'acs_bg.json'
    if cached.exists():  # never pull at run time when a cache exists
        acs, rule = json.loads(cached.read_text()), 'state'
    elif key:
        try:
            acs = fetch_acs(key)
            rule = 'state'
        except Exception as e:
            print('Census key failed, using income fallback:', str(e)[:80])

    if rule == 'state':
        a = [acs.get(g, {}) for g in bg['GEOID']]
        bg['hh'] = [x.get('hh', 0) for x in a]
        bg['nocar'] = [x.get('nocar', 0) for x in a]
        bg['age65'] = [x.get('age65', 0) for x in a]
        bg['pov_pct'] = [x['pov'] / x['pov_hh'] if x.get('pov_hh') else 0 for x in a]
        bg['nocar_pct'] = [n / h if h else 0 for n, h in zip(bg['nocar'], bg['hh'])]
        city_nocar = bg['nocar'].sum() / max(bg['hh'].sum(), 1)
        # HPC: below-average vehicle ownership, or >20% of households below poverty
        bg['low_access'] = (bg['nocar_pct'] > city_nocar) | (bg['pov_pct'] > 0.20)
    else:
        med = bg['BG_MHHI'][bg['BG_MHHI'] > 0].median()
        bg['low_access'] = (bg['BG_MHHI'] > 0) & (bg['BG_MHHI'] < med)
        bg['nocar_pct'] = None
        bg['age65'] = None

    nb = gpd.read_file(DATA / 'raw' / 'neighborhoods.geojson').to_crs(26986)
    ncol = [c for c in nb.columns if 'name' in c.lower()][0]
    cent = gpd.GeoDataFrame(geometry=bg.geometry.representative_point(), crs=26986)
    bg['hood'] = gpd.sjoin(cent, nb[[ncol, 'geometry']], how='left', predicate='within')[ncol].values
    bg['radius_m'] = bg['low_access'].map({True: 0.5 * MILE, False: 1.0 * MILE})
    return bg, ph, closed, rule


def main():
    bg, ph, closed, rule = prepare()
    dpath = DATA / 'bg_districts.json'
    districts = json.loads(dpath.read_text()) if dpath.exists() else {}

    props = []
    for _, b in bg.iterrows():
        p = {'GEOID': b['GEOID'], 'hood': b['hood'], 'pop': int(b['TOTAL_POP'] or 0),
             'low_access': bool(b['low_access']),
             'lim_eng': round(float(b['LIMENGHHPCT'] or 0), 1),
             'nocar_pct': None if b['nocar_pct'] is None else round(float(b['nocar_pct']) * 100, 1),
             'age65': None if b['age65'] is None else int(b['age65'])}
        for r in RADII:
            p[f's_{r:g}'] = status_at(b.geometry, ph, r * MILE)[1]
        r_state = 0.5 if b['low_access'] else 1.0
        p['s_state'] = p[f's_{r_state:g}']
        p.update(districts.get(b['GEOID'], {}))
        props.append(p)

    out = gpd.GeoDataFrame(props, geometry=bg.geometry.simplify(8), crs=26986).to_crs(4326)
    out.to_file(DATA / 'bg_out.geojson', driver='GeoJSON')
    meta = {'rule': rule, 'radii': RADII,
            'pharmacies': [{'name': r['name'], 'lat': r['lat'], 'lon': r['lon'], 'source': r['source']} for _, r in ph.iterrows()],
            'closed': closed}
    (DATA / 'map_meta.json').write_text(json.dumps(meta))

    tot = out['pop'].sum()
    print('low-access rule:', rule)
    for s in ['desert', 'near-desert', 'covered']:
        n = out.loc[out.s_state == s, 'pop'].sum()
        print(f'{s:12s} {n:7d} people ({n / tot * 100:.1f}%)')


if __name__ == '__main__':
    main()

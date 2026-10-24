# 보스턴 외 장소의 대체 후보지(보건소·대형 마트)와 보행망을 받아 data/raw/places/에 캐시하는 스크립트.
import json, pickle, sys, time, warnings
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import osmnx as ox
from shapely.ops import unary_union
from places import BG_FILE, PLACE, RAW, SITES_FILE, SLUG, WALK_FILE

MILE = 1609.344


def retry(fn, tries=5):  # noqa: C901
    delay = 5
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            print(f'  retry {i + 1}/{tries} after {delay}s ({str(e)[:100]})', file=sys.stderr)
            if i == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    return None


def area(buffer_mi):
    bg = gpd.read_file(BG_FILE).to_crs(26986)
    poly = unary_union(list(bg.geometry)).buffer(buffer_mi * MILE)
    return gpd.GeoSeries([poly], crs=26986)


def sites():
    reach = area(2).iloc[0]
    rows = []
    chc = gpd.read_file(RAW / 'chc_raw.geojson').to_crs(26986)
    for _, c in chc[chc.within(reach)].iterrows():
        p = gpd.GeoSeries([c.geometry], crs=26986).to_crs(4326).iloc[0]
        rows.append({'name': c['NAME'], 'kind': 'health_center', 'lat': round(p.y, 6), 'lon': round(p.x, 6),
                     'address': f"{c['ADDRESS']}, {c['MUNICIPALITY'].strip()}", 'source': 'MassGIS Community Health Centers'})
    # Supermarkets: a store that could add a pharmacy counter. Matters most where there is no health center.
    poly = area(2).to_crs(4326).iloc[0]
    try:
        sm = retry(lambda: ox.features_from_polygon(poly, tags={'shop': 'supermarket'}), tries=2)
    except Exception as e:  # Overpass down: health centers only, rerun later to add supermarkets
        print('supermarkets skipped:', str(e)[:80])
        sm = gpd.GeoDataFrame(columns=['name', 'geometry'], geometry='geometry')
    sm = sm[sm.geometry.notna()]
    for _, s in sm.iterrows():
        if not isinstance(s.get('name'), str):
            continue
        p = s.geometry.representative_point()
        addr = ' '.join(str(s.get(k)) for k in ['addr:housenumber', 'addr:street'] if isinstance(s.get(k), str)) or None
        rows.append({'name': s['name'], 'kind': 'supermarket', 'lat': round(p.y, 6), 'lon': round(p.x, 6),
                     'address': addr, 'source': 'OpenStreetMap shop=supermarket'})
    SITES_FILE.write_text(json.dumps({'sites': rows}, indent=0))
    print(f"{PLACE['name']}: {sum(r['kind'] == 'health_center' for r in rows)} health centers, "
          f"{sum(r['kind'] == 'supermarket' for r in rows)} supermarkets")


def walk_graph():
    poly = area(2).to_crs(4326).iloc[0]
    G = retry(lambda: ox.graph_from_polygon(poly, network_type='walk'))
    with open(WALK_FILE, 'wb') as f:
        pickle.dump(G, f)
    print(f"{PLACE['name']} walk graph: {G.number_of_nodes()} nodes")


def main():
    assert SLUG != 'boston', 'Boston uses fetch_sites.py and fetch_walk_graph.py'
    sites()
    try:
        walk_graph()
    except Exception as e:  # walk.py falls back to straight-line x 1.3, labeled as an estimate
        print('walk graph skipped:', str(e)[:80])
    (RAW / 'places' / f'{SLUG}_extras.meta.json').write_text(json.dumps({
        'dataset': 'MassGIS community health centers + OpenStreetMap supermarkets within 2 mi; OpenStreetMap walk network',
        'function': 'scripts/fetch_place_extras.py:main', 'pulled': datetime.now(timezone.utc).isoformat(timespec='seconds')}))


if __name__ == '__main__':
    main()

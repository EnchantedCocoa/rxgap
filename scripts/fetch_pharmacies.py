# 5개 카운티 OSM 약국을 받아 캐시에 저장하는 스크립트.
import json, time, sys, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
import osmnx as ox

COUNTIES = [
    'Suffolk County, Massachusetts, USA',
    'Middlesex County, Massachusetts, USA',
    'Norfolk County, Massachusetts, USA',
    'Essex County, Massachusetts, USA',
    'Plymouth County, Massachusetts, USA',
]
TAGS = {'amenity': 'pharmacy', 'healthcare': 'pharmacy'}
OUT = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'pharmacies.json'


def fetch(place, tries=5):
    delay = 3
    for i in range(tries):
        try:
            return ox.features_from_place(place, tags=TAGS)
        except Exception as e:
            msg = str(e)[:120]
            print(f'  retry {i+1}/{tries} after {delay}s ({msg})', file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f'failed: {place}')


def main():
    feats = []
    seen = set()
    for c in COUNTIES:
        g = fetch(c)
        g = g[g.geometry.notna()].copy()
        g['lon'] = g.geometry.representative_point().x
        g['lat'] = g.geometry.representative_point().y
        n = 0
        for _, r in g.iterrows():
            lon, lat = round(float(r['lon']), 6), round(float(r['lat']), 6)
            key = (lon, lat)
            if key in seen:
                continue
            seen.add(key)
            name = r.get('name')
            if name is None or (isinstance(name, float)):
                name = None
            feats.append({'name': name, 'lat': lat, 'lon': lon})
            n += 1
        print(f'{c}: +{n} (total {len(feats)})')
    OUT.write_text(json.dumps({'pharmacies': feats}, indent=0))
    print(f'wrote {len(feats)} pharmacies -> {OUT}')


if __name__ == '__main__':
    main()

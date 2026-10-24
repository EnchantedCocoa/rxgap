# 5개 카운티 OSM 약국을 받아 주소/식별자 포함 캐시에 저장하는 스크립트.
import json, time, sys, shutil, os, warnings
from datetime import datetime, timezone
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
DATA = Path(__file__).resolve().parent.parent / 'data' / 'raw'
OUT = DATA / 'pharmacies.json'
META = DATA / 'pharmacies.meta.json'


def _clean(v):
    # 결측(NaN/None)을 None 으로 정규화하는 헬퍼.
    if v is None:
        return None
    if isinstance(v, float):
        return None
    s = str(v).strip()
    return s if s else None


def _county_name(place):
    # 'Suffolk County, ...' -> 'Suffolk' 로 카운티 라벨을 뽑는 헬퍼.
    return place.split(' County')[0].strip()


def _address(r):
    # OSM addr:* 태그들로 주소 문자열을 조립(없으면 None).
    hn = _clean(r.get('addr:housenumber'))
    st = _clean(r.get('addr:street'))
    city = _clean(r.get('addr:city'))
    zp = _clean(r.get('addr:postcode'))
    line1 = ' '.join(p for p in [hn, st] if p)
    tail = ' '.join(p for p in [city, zp] if p)
    full = ', '.join(p for p in [line1, tail] if p)
    return full if full else None


def _osm_id(r):
    # GeoDataFrame 의 (element_type, osmid) 멀티인덱스에서 'node/123' 형태를 만든다.
    name = r.name  # Series 의 index 값 = (element_type, osmid)
    if isinstance(name, tuple) and len(name) == 2:
        et, oid = name
        return f'{et}/{oid}'
    return None


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
    # 덮어쓰기 전에 기존 파일을 스크래치로 백업.
    scratch = os.environ.get('KIROCREW_SCRATCH', '/tmp')
    backup = Path(scratch) / 'pharmacies.old.json'
    had_old = OUT.exists()
    if had_old:
        shutil.copy2(OUT, backup)
        print(f'backed up old -> {backup}', file=sys.stderr)

    try:
        feats = []
        seen = set()
        for c in COUNTIES:
            g = fetch(c)
            g = g[g.geometry.notna()].copy()
            g['_lon'] = g.geometry.representative_point().x
            g['_lat'] = g.geometry.representative_point().y
            county = _county_name(c)
            n = 0
            for _, r in g.iterrows():
                lon, lat = round(float(r['_lon']), 6), round(float(r['_lat']), 6)
                key = (lon, lat)
                if key in seen:
                    continue
                seen.add(key)
                feats.append({
                    'name': _clean(r.get('name')),
                    'lat': lat,
                    'lon': lon,
                    'address': _address(r),
                    'osm_id': _osm_id(r),
                    'brand': _clean(r.get('brand')),
                    'county': county,
                })
                n += 1
            print(f'{c}: +{n} (total {len(feats)})')
    except Exception as e:
        if had_old:
            shutil.copy2(backup, OUT)
            print(f'FETCH FAILED ({e}); restored old -> {OUT}', file=sys.stderr)
        else:
            print(f'FETCH FAILED ({e}); no prior file to restore', file=sys.stderr)
        raise

    OUT.write_text(json.dumps({'pharmacies': feats}, indent=0))
    meta = {
        'dataset': 'OpenStreetMap amenity=pharmacy|healthcare=pharmacy, 5 counties (Suffolk, Middlesex, Norfolk, Essex, Plymouth)',
        'source': 'Overpass API via osmnx',
        'function': 'scripts/fetch_pharmacies.py:main',
        'pulled': datetime.now(timezone.utc).isoformat(),
        'count': len(feats),
    }
    META.write_text(json.dumps(meta, indent=2))
    print(f'wrote {len(feats)} pharmacies -> {OUT}')
    print(f'wrote meta -> {META}')


if __name__ == '__main__':
    main()

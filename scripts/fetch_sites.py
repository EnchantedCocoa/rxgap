# 대체 약국 후보지(건강센터·지하철역·수동 점포)를 모아 sites.json으로 만드는 스크립트.
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
MANUAL = ROOT / 'data' / 'manual'
RAW.mkdir(parents=True, exist_ok=True)
MANUAL.mkdir(parents=True, exist_ok=True)

# MassGIS Community Health Centers (ArcGIS Online hosted feature layer, Dec 2024)
CHC_URL = (
    'https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/'
    'Community_Health_Centers/FeatureServer/0/query'
    '?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=geojson'
)
CHC_DATASET = 'MassGIS Community Health Centers (Hosted Feature Layer)'

# MBTA rapid transit stations (MassGIS AGOL MapServer)
MBTA_URL = (
    'https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/'
    'MBTA_Rapid_Transit/MapServer/0/query'
    '?where=1%3D1&outFields=STATION,LINE&returnGeometry=true&outSR=4326&f=geojson'
)
MBTA_DATASET = 'MassGIS AGOL MBTA Rapid Transit stations'

BOSTON_BG = RAW / 'boston_bg.geojson'
BUFFER_MILES = 2.0
METERS_PER_MILE = 1609.344


def fetch_geojson(url, cache_path, tries=5):
    """네트워크 재시도(지수 백오프)로 받아 캐시; 실패 시 기존 캐시로 폴백."""
    delay = 3
    last_err = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            data = r.json()
            if 'error' in data:
                raise RuntimeError(str(data['error'])[:160])
            cache_path.write_text(json.dumps(data))
            return data, 'network'
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:140]
            print(f'  retry {i + 1}/{tries} after {delay}s ({last_err})', file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    if cache_path.exists():
        print(f'  network failed; using cached {cache_path.name}', file=sys.stderr)
        return json.loads(cache_path.read_text()), 'cache'
    raise RuntimeError(f'failed and no cache: {url} ({last_err})')


def build_boundary():
    """보스턴 블록그룹 union을 2마일 버퍼한 경계(EPSG:4326 폴리곤)."""
    g = gpd.read_file(BOSTON_BG)
    if g.crs is None:
        g = g.set_crs(4326)
    g = g.to_crs(26986)
    buffered = unary_union(g.geometry.values).buffer(BUFFER_MILES * METERS_PER_MILE)
    return gpd.GeoSeries([buffered], crs=26986).to_crs(4326).iloc[0]


def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def chc_sites(features):
    out = []
    for f in features:
        geom = f.get('geometry')
        if not geom:
            continue
        lon, lat = geom['coordinates'][0], geom['coordinates'][1]
        p = f.get('properties', {})
        parts = [clean(p.get('ADDRESS')), clean(p.get('MUNICIPALITY')),
                 'MA', clean(p.get('ZIP_CODE'))]
        address = ', '.join([x for x in parts if x]) or None
        out.append({
            'name': clean(p.get('NAME')),
            'kind': 'health_center',
            'lat': round(float(lat), 6),
            'lon': round(float(lon), 6),
            'address': address,
            'source': CHC_DATASET,
        })
    return out


def mbta_sites(features):
    """역이 노선별로 중복 등장 -> 역 이름 기준으로 병합하고 노선을 이름에 합친다."""
    by_key = {}
    order = []
    for f in features:
        geom = f.get('geometry')
        if not geom:
            continue
        lon, lat = float(geom['coordinates'][0]), float(geom['coordinates'][1])
        p = f.get('properties', {})
        station = clean(p.get('STATION')) or 'Unknown'
        line = clean(p.get('LINE'))
        key = station.lower()  # 환승역은 노선별 좌표가 미세하게 달라 이름으로 병합한다.
        if key not in by_key:
            by_key[key] = {'station': station, 'lats': [], 'lons': [], 'lines': []}
            order.append(key)
        by_key[key]['lats'].append(lat)
        by_key[key]['lons'].append(lon)
        if line and line not in by_key[key]['lines']:
            by_key[key]['lines'].append(line)
    out = []
    for key in order:
        rec = by_key[key]
        lines = sorted({ln.title() for ln in rec['lines']})
        name = rec['station']
        if lines:
            name = f"{rec['station']} ({', '.join(lines)})"
        out.append({
            'name': name,
            'kind': 'mbta_station',
            'lat': round(sum(rec['lats']) / len(rec['lats']), 6),
            'lon': round(sum(rec['lons']) / len(rec['lons']), 6),
            'address': None,
            'source': MBTA_DATASET,
        })
    return out


def manual_sites(path):
    if not path.exists():
        path.write_text('name,kind,lat,lon,address,source_url\n')
        return []
    out = []
    with path.open() as fh:
        for row in csv.DictReader(fh):
            lat, lon = clean(row.get('lat')), clean(row.get('lon'))
            if not lat or not lon:
                continue
            out.append({
                'name': clean(row.get('name')),
                'kind': 'storefront',
                'lat': round(float(lat), 6),
                'lon': round(float(lon), 6),
                'address': clean(row.get('address')),
                'source': clean(row.get('source_url')) or 'manual',
            })
    return out


def main():
    now = datetime.now(timezone.utc).isoformat()

    chc_raw, chc_origin = fetch_geojson(CHC_URL, RAW / 'chc_raw.geojson')
    mbta_raw, mbta_origin = fetch_geojson(MBTA_URL, RAW / 'mbta_raw.geojson')

    boundary = build_boundary()
    prepared = boundary  # shapely contains handles point test

    sites = []
    kept_counts = {'health_center': 0, 'mbta_station': 0, 'storefront': 0}
    dropped_counts = {'health_center': 0, 'mbta_station': 0, 'storefront': 0}

    for rec in (chc_sites(chc_raw.get('features', []))
                + mbta_sites(mbta_raw.get('features', []))
                + manual_sites(MANUAL / 'candidate_sites.csv')):
        pt = shape({'type': 'Point', 'coordinates': [rec['lon'], rec['lat']]})
        if prepared.contains(pt) or prepared.intersects(pt):
            sites.append(rec)
            kept_counts[rec['kind']] += 1
        else:
            dropped_counts[rec['kind']] += 1

    out_path = ROOT / 'data' / 'raw' / 'sites.json'
    out_path.write_text(json.dumps({'sites': sites}, indent=0))

    meta = {
        'health_center': {'dataset': CHC_DATASET, 'url': CHC_URL, 'pulled': now},
        'mbta_station': {'dataset': MBTA_DATASET, 'url': MBTA_URL, 'pulled': now},
        'storefront': {'dataset': 'manual'},
        'function': 'scripts/fetch_sites.py:main',
    }
    (RAW / 'sites.meta.json').write_text(json.dumps(meta, indent=2))

    print(f'chc source: {chc_origin}, mbta source: {mbta_origin}')
    print(f'kept within 2mi: {kept_counts} (total {len(sites)})')
    print(f'dropped outside 2mi: {dropped_counts}')
    print(f'wrote {out_path}')


if __name__ == '__main__':
    main()

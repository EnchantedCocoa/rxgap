# 원본 데이터의 출처·수집일 메타 파일을 data/provenance.json 하나로 모으는 스크립트.
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'


def mtime(p):
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')


def main():
    out = {}
    for m in sorted(RAW.glob('*.meta.json')):
        out[m.name.removesuffix('.meta.json')] = json.loads(m.read_text())
    # Files fetched before the sidecar convention: pull date = file time.
    out['block_groups'] = {
        'dataset': 'MassGIS EJ2020 block groups, MUNICIPALITY=Boston (2020 GEOIDs)',
        'url': 'https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/EJ2020/MapServer/0',
        'function': 'scripts/analyze_bg.py:prepare', 'pulled': mtime(RAW / 'boston_bg.geojson')}
    out['acs'] = {
        'dataset': 'ACS 2022 5-year, block group: B25044 (vehicles), B01001 (age 65+), B17017 (poverty)',
        'url': 'https://api.census.gov/data/2022/acs/acs5',
        'function': 'scripts/analyze_bg.py:fetch_acs', 'pulled': mtime(RAW / 'acs_bg.json')}
    out['neighborhoods'] = {
        'dataset': 'Boston neighborhood boundaries (Analyze Boston)',
        'function': 'scripts/analyze_bg.py:prepare', 'pulled': mtime(RAW / 'neighborhoods.geojson')}
    out['closures'] = {
        'dataset': 'Hand-kept closure list with a source URL per row',
        'file': 'data/manual/closures.csv', 'function': 'scripts/analyze_bg.py:load_pharmacies',
        'pulled': mtime(ROOT / 'data' / 'manual' / 'closures.csv')}
    out['openings'] = {
        'dataset': 'Hand-kept list of pharmacies OpenStreetMap is missing, with a source URL per row',
        'file': 'data/manual/openings.csv', 'function': 'scripts/analyze_bg.py:load_pharmacies',
        'pulled': mtime(ROOT / 'data' / 'manual' / 'openings.csv')}
    (ROOT / 'data' / 'provenance.json').write_text(json.dumps(out, indent=1))
    print(f'{len(out)} sources -> data/provenance.json')


if __name__ == '__main__':
    main()

# 보스턴과 인접 우편번호의 NPI 소매 약국을 받아 주소를 좌표로 바꾸고 data/raw/npi_retail.json으로 저장하는 스크립트.
import csv, io, json, time
from datetime import datetime, timezone
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parent.parent / 'data' / 'raw'
OUT = RAW / 'npi_retail.json'
NPI = 'https://npiregistry.cms.hhs.gov/api/'
GEOCODER = 'https://geocoding.geo.census.gov/geocoder/locations/addressbatch'
RETAIL = '3336C0003X'  # Community/Retail Pharmacy
PHARMACY = '333600000X'  # generic 'Pharmacy': chains (CVS, Walgreens) use this as primary
NOT_RETAIL = {'3336I0012X': 'institutional', '3336M0002X': 'mail order', '3336S0011X': 'specialty',
              '3336L0003X': 'long-term care', '3336H0001X': 'home infusion', '3336N0007X': 'nuclear'}
# Boston ZIPs plus neighbors whose stores can sit within a mile of the city line.
ZIPS = [f'021{n:02d}' for n in range(8, 38)] + ['02163', '02199', '02210', '02215'] + [
    '02138', '02139', '02140', '02141', '02142', '02143', '02144', '02145', '02148', '02149', '02150',
    '02151', '02152', '02169', '02170', '02171', '02186', '02026', '02445', '02446', '02447', '02458',
    '02459', '02467', '02472', '02368', '02021', '02090', '02494']


def get(params, tries=4):
    for i in range(tries):
        try:
            return requests.get(NPI, params=params, timeout=30).json()
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(f'NPI failed: {params}')


def pull():
    rows = {}
    for z in ZIPS:
        for skip in range(0, 1001, 200):
            r = get({'version': '2.1', 'enumeration_type': 'NPI-2', 'taxonomy_description': 'Pharmacy',
                     'postal_code': z, 'state': 'MA', 'limit': 200, 'skip': skip}).get('results', [])
            for x in r:
                loc = next((a for a in x['addresses'] if a['address_purpose'] == 'LOCATION'), None)
                if not loc or loc['state'] != 'MA':
                    continue
                codes = {t['code'] for t in x.get('taxonomies', [])}
                primary = next((t['code'] for t in x.get('taxonomies', []) if t.get('primary')), None)
                rows[x['number']] = {
                    'npi': x['number'], 'name': x['basic'].get('organization_name', ''),
                    'dba': next((o['organization_name'] for o in x.get('other_names', []) if o.get('type') == 'Doing Business As'), None),
                    'address': loc['address_1'], 'city': loc['city'], 'zip': loc['postal_code'][:5],
                    'primary': primary, 'retail': RETAIL in codes, 'other_kinds': sorted(NOT_RETAIL[c] for c in codes if c in NOT_RETAIL),
                    'updated': x['basic'].get('last_updated'), 'status': x['basic'].get('status')}
            if len(r) < 200:
                break
    return list(rows.values())


def geocode(rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow([r['npi'], r['address'], r['city'], 'MA', r['zip']])
    res = requests.post(GEOCODER, files={'addressFile': ('a.csv', buf.getvalue())},
                        data={'benchmark': 'Public_AR_Current'}, timeout=300).text
    pts = {}
    for line in csv.reader(io.StringIO(res)):
        if len(line) >= 6 and line[2] == 'Match':
            lon, lat = map(float, line[5].split(','))
            pts[line[0]] = (lat, lon)
    for r in rows:
        r['lat'], r['lon'] = pts.get(r['npi'], (None, None))
    return rows


def main():
    rows = geocode([r for r in pull() if r['status'] == 'A' and r['retail']
                     and r['primary'] in (RETAIL, PHARMACY) and not r['other_kinds']])
    OUT.write_text(json.dumps({'pharmacies': rows}, indent=0))
    (RAW / 'npi_retail.meta.json').write_text(json.dumps({
        'dataset': 'NPI Registry, active organizations listing Community/Retail Pharmacy (3336C0003X), primary Retail or Pharmacy, no institutional/mail/specialty/LTC codes, Boston + neighboring ZIPs, geocoded with the US Census geocoder',
        'url': NPI, 'function': 'scripts/fetch_npi_retail.py:main', 'count': len(rows),
        'pulled': datetime.now(timezone.utc).isoformat(timespec='seconds')}, indent=2))
    ok = sum(r['lat'] is not None for r in rows)
    print(f'{len(rows)} active retail NPI pharmacies, {ok} geocoded -> {OUT}')


if __name__ == '__main__':
    main()

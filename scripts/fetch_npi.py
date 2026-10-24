# NPI Registry에서 보스턴 소매약국을 받아 OSM 데이터와 대조(dry-run)하는 스크립트.
import json, time, sys, os, re, hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
CACHE = ROOT / 'cache'
API = 'https://npiregistry.cms.hhs.gov/api/'

# NPI Registry는 한 쿼리당 skip 최대 1000(= 1200건)까지만 페이지네이션 허용.
BASE_PARAMS = {
    'version': '2.1',
    'enumeration_type': 'NPI-2',
    'taxonomy_description': 'Community/Retail Pharmacy',
    'state': 'MA',
    'limit': 200,
}
# 자체 USPS city 이름을 가지는 보스턴 동네들(검색을 넓히기 위해 각각 질의).
CITIES = [
    'BOSTON', 'DORCHESTER', 'ROXBURY', 'MATTAPAN', 'HYDE PARK', 'ROSLINDALE',
    'WEST ROXBURY', 'JAMAICA PLAIN', 'EAST BOSTON', 'CHARLESTOWN',
    'SOUTH BOSTON', 'BRIGHTON', 'ALLSTON', 'DORCHESTER CENTER',
]


def _cache_path(params):
    key = hashlib.sha1(urlencode(sorted(params.items())).encode()).hexdigest()
    return CACHE / f'npi_{key}.json'


def _get(params, tries=5):
    cp = _cache_path(params)
    if cp.exists():
        return json.loads(cp.read_text())
    delay = 2
    for i in range(tries):
        try:
            r = requests.get(API, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            cp.write_text(json.dumps(data))
            return data
        except Exception as e:
            print(f'  retry {i+1}/{tries} after {delay}s ({str(e)[:100]})', file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f'NPI fetch failed: {params.get("city")}')


def _location(result):
    # practice LOCATION 주소를 고르고 없으면 아무 주소나 대체.
    addrs = result.get('addresses') or []
    loc = next((a for a in addrs if a.get('address_purpose') == 'LOCATION'), None)
    return loc or (addrs[0] if addrs else {})


def fetch_all():
    pharmacies = {}
    for city in CITIES:
        got_city = 0
        for skip in range(0, 1001, 200):
            params = dict(BASE_PARAMS, city=city)
            if skip:
                params['skip'] = skip
            data = _get(params)
            results = data.get('results') or []
            if not results:
                break
            for res in results:
                npi = res.get('number')
                if not npi:
                    continue
                basic = res.get('basic') or {}
                loc = _location(res)
                street = ' '.join(x for x in [loc.get('address_1'), loc.get('address_2')] if x).strip()
                pharmacies[str(npi)] = {
                    'npi': str(npi),
                    'name': basic.get('organization_name') or basic.get('name'),
                    'address': street,
                    'city': loc.get('city'),
                    'state': loc.get('state'),
                    'postal_code': (loc.get('postal_code') or '')[:5],
                    'status': basic.get('status'),
                }
                got_city += 1
            if len(results) < 200:
                break
        print(f'{city}: +{got_city} (unique total {len(pharmacies)})', file=sys.stderr)
    return list(pharmacies.values())


# ---------- 정규화 + 매칭 유틸 ----------
_SUFFIX = re.compile(r'\b(pharmacy|pharmacies|drug|drugs|store|stores|inc|llc|corp|co|the)\b')
_STREET_SUFFIX = re.compile(
    r'\b(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|place|pl|'
    r'square|sq|court|ct|parkway|pkwy|highway|hwy|terrace|ter|way)\b')


def norm_name(s):
    if not s:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = _SUFFIX.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def norm_addr(s):
    if not s:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = _STREET_SUFFIX.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def street_num(s):
    m = re.match(r'\s*(\d+)', s or '')
    return m.group(1) if m else ''


def match_dryrun(npi_list, osm_list):
    # OSM 레코드: name/lat/lon (+ 선택적 address). NPI와 토큰셋 비율로 대조.
    osm_prep = []
    for o in osm_list:
        osm_prep.append({
            'name': o.get('name'),
            'nname': norm_name(o.get('name')),
            'naddr': norm_addr(o.get('address')),
            'snum': street_num(o.get('address')),
            'lat': o.get('lat'), 'lon': o.get('lon'),
        })
    NAME_TH, COMBO_TH = 82, 80
    matched_osm = set()
    both, npi_only = [], []
    for n in npi_list:
        nn = norm_name(n['name'])
        na = norm_addr(n['address'])
        nsnum = street_num(n['address'])
        best, best_i = 0.0, -1
        for i, o in enumerate(osm_prep):
            if not o['nname']:
                continue
            name_sc = fuzz.token_set_ratio(nn, o['nname'])
            if o['naddr'] and na:
                addr_sc = fuzz.token_set_ratio(na, o['naddr'])
                num_bonus = 10 if (nsnum and o['snum'] and nsnum == o['snum']) else 0
                score = 0.6 * name_sc + 0.4 * addr_sc + num_bonus
                hit = score >= COMBO_TH and name_sc >= 55
            else:
                score = name_sc
                hit = name_sc >= NAME_TH
            if hit and score > best:
                best, best_i = score, i
        if best_i >= 0:
            matched_osm.add(best_i)
            both.append({'npi': n['npi'], 'npi_name': n['name'],
                         'osm_name': osm_prep[best_i]['name'], 'score': round(best, 1)})
        else:
            npi_only.append(n)
    osm_only = [osm_list[i] for i in range(len(osm_list)) if i not in matched_osm]
    return both, osm_only, npi_only


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    pharmacies = fetch_all()
    pulled = datetime.now(timezone.utc).isoformat()

    (RAW / 'npi.json').write_text(json.dumps({'pharmacies': pharmacies}, indent=0))
    meta = {
        'dataset': 'NPI Registry NPI-2 Community/Retail Pharmacy (Boston, MA)',
        'url': API + '?' + urlencode(dict(BASE_PARAMS, city='BOSTON')),
        'pulled': pulled,
        'function': 'scripts/fetch_npi.py:main',
        'count': len(pharmacies),
        'cities_queried': CITIES,
    }
    (RAW / 'npi.meta.json').write_text(json.dumps(meta, indent=2))
    print(f'wrote {len(pharmacies)} NPI pharmacies -> {RAW / "npi.json"}')

    # dry-run 대조 (프로젝트 데이터 파일에는 쓰지 않음)
    osm = json.loads((RAW / 'pharmacies.json').read_text()).get('pharmacies', [])
    both, osm_only, npi_only = match_dryrun(pharmacies, osm)

    scratch = Path(os.environ.get('KIROCREW_SCRATCH', '/tmp'))
    out = {
        'summary': {'both': len(both), 'osm_only': len(osm_only), 'npi_only': len(npi_only),
                    'npi_total': len(pharmacies), 'osm_total': len(osm)},
        'both': both,
        'npi_only': npi_only,
        'osm_only': osm_only,
    }
    (scratch / 'npi_match.json').write_text(json.dumps(out, indent=2))
    print(f'match: both={len(both)} osm_only={len(osm_only)} npi_only={len(npi_only)} '
          f'(npi_total={len(pharmacies)} osm_total={len(osm)})')
    print(f'wrote dry-run -> {scratch / "npi_match.json"}')
    for e in npi_only[:5]:
        print(f'  NPI-only: {e["name"]} | {e["address"]} {e["postal_code"]} | {e["status"]}')


if __name__ == '__main__':
    main()

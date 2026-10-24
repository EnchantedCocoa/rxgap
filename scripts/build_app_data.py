# 화면에 나오는 모든 숫자와 출처를 data/app_data.json 하나로 묶는 스크립트.
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
RULES = {'state': 's_state', 'half': 's_0.5', 'one': 's_1'}

# Each on-screen number names the function that made it and the raw sources behind it.
PROV = {
    'headline': ('scripts/analyze_bg.py:main', ['block_groups', 'acs', 'acs_state', 'pharmacies', 'closures', 'openings']),
    'store': ('scripts/rank.py:main', ['block_groups', 'acs', 'pharmacies', 'closures', 'openings']),
    'lim_eng_hh': ('scripts/build_app_data.py:store_rows', ['block_groups']),
    'walk': ('scripts/walk.py:nearest3', ['walk', 'pharmacies']),
    'siting': ('scripts/siting.py:score + best_set (PuLP max-coverage)', ['sites', 'pharmacies', 'block_groups', 'acs']),
    'officials': ('scripts/route.py:main', ['districts']),
    'block': ('scripts/analyze_bg.py:main', ['block_groups', 'acs']),
    'globe': ('Boston Globe, July 2024 (reported figure)', []),
    'town': ('Massachusetts Health Policy Commission, DataPoints 31 public block-group dataset (scripts/build_towns.py)', ['hpc']),
    'low_access_share': ('scripts/build_app_data.py:main', ['block_groups', 'acs']),
}


def officials():
    out = {}
    with open(DATA / 'manual' / 'officials.csv') as f:
        for r in csv.DictReader(f):
            out[(r['district_type'], r['district_id'])] = r
    return out


def store_rows(stores, raw_bg, offs):
    title = {'council': 'Councilor', 'house': 'Rep.', 'senate': 'Sen.'}
    rows = []
    for s in stores:
        lim = 0
        people_by = {}
        for b in s['lost']:
            p = raw_bg[b['GEOID']]
            lim += round((p['LIMENGHHPCT'] or 0) / 100 * (p['TOTALHH'] or 0))
            for kind, did in b['districts'].items():
                people_by[(kind, did)] = people_by.get((kind, did), 0) + b['pop']
        offs_rows = []
        for (kind, did), n in sorted(people_by.items(), key=lambda kv: (list(title).index(kv[0][0]), -kv[1])):
            o = offs.get((kind, did), {})
            label = f'District {did}' if kind == 'council' else did
            offs_rows.append({'kind': kind, 'district': label, 'title': title[kind],
                              'name': o.get('name') or 'Name not verified',
                              'url': o.get('source_url'), 'people': n})
        rows.append({**{k: s[k] for k in ['rank', 'name', 'address', 'lat', 'lon', 'people',
                                          'age65', 'nocar_hh', 'hoods', 'block_groups', 'lost']},
                     'lim_eng_hh': lim, 'officials': offs_rows,
                     'next_walk_max': max((b['nearest'][0]['walk_min'] for b in s['lost'] if b['nearest']),
                                          default=None)})
    return rows


def main():
    bg = json.loads((DATA / 'bg_out.geojson').read_text())['features']
    raw_bg = {f['properties']['GEOID']: f['properties']
              for f in json.loads((DATA / 'raw' / 'boston_bg.geojson').read_text())['features']}
    rank = json.loads((DATA / 'cant_lose.json').read_text())
    sites = json.loads((DATA / 'sites_out.json').read_text())
    meta = json.loads((DATA / 'map_meta.json').read_text())

    total = sum(f['properties']['pop'] for f in bg)
    headline = {}
    for rule, prop in RULES.items():
        n = {s: sum(f['properties']['pop'] for f in bg if f['properties'][prop] == s)
             for s in ['desert', 'near-desert', 'covered']}
        headline[rule] = {'desert': n['desert'], 'near': n['near-desert'], 'covered': n['covered'],
                          'total': total, 'desert_pct': round(n['desert'] / total * 100)}

    low = sum(1 for f in bg if f['properties']['low_access'])
    hpc = {r['GEOID']: r for r in csv.DictReader(open(DATA / 'raw' / 'hpc' / 'hpc_bg_with_town.csv'))}
    hmap = {'Pharmacy deserts': 'desert', 'Near deserts': 'near-desert', 'Non-deserts': 'covered'}
    agree = sum(f['properties']['pop'] for f in bg
                if hmap.get(hpc.get(f['properties']['GEOID'], {}).get('Category (HPC)')) == f['properties']['s_state'])
    hpc_desert = sum(int(r['POP20']) for r in hpc.values() if r['town'] == 'Boston' and r['Category (HPC)'] == 'Pharmacy deserts')
    added = sum(1 for p in meta['pharmacies'] if p.get('source') and p['source'] != 'OpenStreetMap')
    ranked = {(s['lat'], s['lon']): s['rank'] for s in rank['stores']}
    out = {
        'rule': rank['rule'],
        'rules': RULES,
        'headline': headline,
        'validation': {'desert_pop': headline['state']['desert'], 'globe_pop': 15000,
                       'globe_date': 'July 2024', 'tufts_date': 'October 2025',
                       'hpc_report': 'DataPoints 31, October 2025', 'area_pct': '15%',
                       'hpc_pop': hpc_desert, 'hpc_date': 'June 2025', 'added_stores': added,
                       'hpc_agree': f'{round(agree / total * 100)}%',
                       'at_risk_pct': round((headline['state']['desert'] + headline['state']['near']) / total * 100),
                       'low_access_share': f'{round(low / len(bg) * 100)}%'},
        'stores': [{**r, 'sites': sites[str(r['rank'])]} for r in store_rows(rank['stores'], raw_bg, officials())],
        'pharmacies': [{'id': i, 'name': p['name'] or 'Pharmacy', 'lat': p['lat'], 'lon': p['lon'], 'source': p.get('source'),
                        'rank': ranked.get((p['lat'], p['lon']))}
                       for i, p in enumerate(meta['pharmacies'])],
        'closed': [{'name': c['name'], 'address': c['address'], 'date': c['date'],
                    'lat': float(c['lat']), 'lon': float(c['lon']), 'source_url': c['source_url']}
                   for c in meta['closed']],
        'prov': {k: {'function': f, 'sources': s} for k, (f, s) in PROV.items()},
        'sources': json.loads((DATA / 'provenance.json').read_text()),
    }
    (DATA / 'app_data.json').write_text(json.dumps(out))
    print(f"app_data.json: {len(out['stores'])} stores, {len(out['pharmacies'])} pharmacies")


if __name__ == '__main__':
    main()

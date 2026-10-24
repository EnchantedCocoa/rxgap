# 편지·브리프·배달 도우미 템플릿에 넣을 사실(facts)을 분석 결과에서 모아 facts.json으로 쓰는 스크립트.
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from places import MANUAL, OUT as DATA, PLACE, SLUG

TITLE = {'council': 'Councilor', 'house': 'Rep.', 'senate': 'Sen.'}
GOV = {'boston': ('the City of Boston', 'la Ciudad de Boston', 'Vil Boston'),
       'springfield': ('the City of Springfield', 'la Ciudad de Springfield', 'Vil Springfield'),
       'plymouth': ('the Town of Plymouth', 'el Municipio de Plymouth', 'Vil Plymouth')}
AGE_CUT = 65  # analyze_bg sums the ACS age bins from 65 up


def policy_facts():
    P = {r['id']: r for r in json.loads((MANUAL / 'policy.json').read_text())}
    return {'pickup_rides_cite': P['pickup_rides']['cite'], 'pt1_days': P['pt1_days']['value'], 'pt1_form': P['pt1_days']['form'],
            'mh_phone': P['mh_phone']['value'], 'mh_office': P['mh_office']['value'],
            'delivery_fee': P['delivery_fee']['value'], 'delivery_fee_year': str(P['delivery_fee']['year']),
            'mail_months': P['mail_months']['value'],
            'closure_notice_days': P['closure_notice']['value'], 'closure_notice_cite': P['closure_notice']['cite']}


def officials_for(districts, offs):
    out = []
    for kind in ('council', 'house', 'senate'):
        did = districts.get(kind)
        if not did or (kind == 'council' and not PLACE['council']):
            continue
        o = offs.get((kind, did), {})
        out.append({'kind': kind, 'id': did, 'title': TITLE[kind], 'name': o.get('name') or 'Name not verified',
                    'district': f'District {did}' if kind == 'council' else did,
                    'address': o.get('office_address') or '', 'url': o.get('source_url') or ''})
    return out


def main():
    D = json.loads((DATA / 'app_data.json').read_text())
    bg = {f['properties']['GEOID']: f['properties'] for f in json.loads((DATA / 'bg_out.geojson').read_text())['features']}
    dist = json.loads((DATA / 'bg_districts.json').read_text())
    extras = json.loads((DATA / 'block_extras.json').read_text())
    with open(MANUAL / 'officials.csv') as f:
        offs = {(r['district_type'], r['district_id']): r for r in csv.DictReader(f)}
    v, h = D['validation'], D['headline']['state']
    gov = GOV[SLUG]
    place = {'place': PLACE['name'], 'place_gov': gov[0], 'place_gov_es': gov[1], 'place_gov_ht': gov[2],
             'hpc_report': v['hpc_report'], 'desert_share': v['area_pct'], 'age_cut': AGE_CUT,
             'place_desert': h['desert'], 'place_near': h['near'], 'walk_estimate': bool(D['place']['walk_estimate']),
             **policy_facts()}
    sample = json.loads((MANUAL / 'sample_addresses.json').read_text()).get(SLUG)  # a public building in a desert, for the letter form
    if sample:
        place.update(sample_address=sample['address'], sample_what=sample['what'], sample_geoid=sample['geoid'])

    briefs = {}
    for s in D['stores']:
        store = {'store_name': s['name'], 'store_address': s['address'] or '', 'store_people': s['people'],
                 'store_age65': s['age65'], 'store_nocar_hh': s['nocar_hh'], 'store_lim_eng_hh': s['lim_eng_hh']}
        sites = [{'name': x['name'], 'address': x['address'] or '', 'gain': x['gain']} for x in s['sites']['top']]
        rows = []
        for o in s['officials']:
            did = o['district'].removeprefix('District ') if o['kind'] == 'council' else o['district']
            blocks = [{'geoid': b['GEOID'], 'hood': bg[b['GEOID']].get('hood') or PLACE['name'], 'pop': b['pop'],
                       **({'near_name': b['nearest'][0]['name'], 'near_min': b['nearest'][0]['walk_min']} if b['nearest'] else {})}
                      for b in s['lost'] if b['districts'].get(o['kind']) == did]
            rows.append({**store, 'official_key': f"{o['kind']}:{did}", 'official_title': o['title'],
                         'official_name': o['name'], 'official_district': o['district'], 'official_url': o['url'] or '',
                         'official_people': o['people'], 'blocks': blocks, 'sites': sites})
        briefs[str(s['rank'])] = rows

    blocks = {}
    for g, p in bg.items():
        hood = p.get('hood') or PLACE['name']
        offl = officials_for(dist.get(g, {}), offs)
        fb = {'geoid': g, 'hood': hood, 'where': PLACE['name'] if hood == PLACE['name'] else f"{hood}, {PLACE['name']}",
              'block_pop': p['pop'], 'is_desert': p['s_state'] == 'desert', 'is_near': p['s_state'] == 'near-desert',
              'officials': offl, 'officials_line': '; '.join(f"{o['title']} {o['name']} ({o['district']})" for o in offl),
              'near_stores': [{**n, 'address': n['address'] or ''} for n in extras[g]['near']]}
        site = None
        if fb['is_near']:
            s = min((s for s in D['stores'] if g in s['block_groups']), key=lambda s: s['rank'])
            fb.update(store_rank=s['rank'], store_name=s['name'], store_address=s['address'] or '',
                      store_people=s['people'], store_age65=s['age65'], store_nocar_hh=s['nocar_hh'])
            site = (s['sites']['top'] or [None])[0]
        elif fb['is_desert']:
            site = extras[g].get('site')
        if site:
            fb.update(site_name=site['name'], site_address=site['address'] or '', site_gain=site['gain'])
        blocks[g] = fb

    (DATA / 'facts.json').write_text(json.dumps({'place': place, 'briefs': briefs, 'blocks': blocks}, ensure_ascii=False))
    print(f"facts.json: {sum(map(len, briefs.values()))} briefs, {len(blocks)} blocks")


if __name__ == '__main__':
    main()

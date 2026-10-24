# 약국 하나가 문을 닫으면 몇 명이 약국 사막에 빠지는지로 순위를 매기는 스크립트.
import json, sys, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import walk
from analyze_bg import DATA, prepare, status_at

TOP = 20


def main():
    bg, ph, _, rule = prepare()
    districts = json.loads((DATA / 'bg_districts.json').read_text())
    base = {i: status_at(b.geometry, ph, b.radius_m)[1] for i, b in bg.iterrows()}
    names = gpd.GeoDataFrame(ph.copy(), geometry=ph.geometry, crs=26986)

    rows = []
    for pi, p in ph.iterrows():
        rest = ph.drop(index=pi)
        # Only block groups this store can reach can change status.
        reach = bg[bg.distance(p.geometry) <= bg.radius_m]
        lost = []
        for bi, b in reach.iterrows():
            if base[bi] != 'desert' and status_at(b.geometry, rest, b.radius_m)[1] == 'desert':
                lost.append(bi)
        if not lost:
            continue
        L = bg.loc[lost]
        detail = []
        for bi in lost:
            b = bg.loc[bi]
            detail.append({
                'GEOID': b['GEOID'], 'pop': int(b['TOTAL_POP'] or 0),
                'age65': int(b['age65'] or 0) if rule == 'state' else None,
                'nocar_hh': int(b['nocar'] or 0) if rule == 'state' else None,
                'lim_eng': round(float(b['LIMENGHHPCT'] or 0), 1),
                'districts': districts.get(b['GEOID'], {}),
                'nearest': walk.nearest3(b.geometry.representative_point(), rest),
            })
        rows.append({
            'name': p['name'] or 'Pharmacy', 'address': p.get('address') or 'address not in OSM',
            'osm_id': p.get('osm_id'), 'source': p.get('source'), 'lat': p['lat'], 'lon': p['lon'],
            'people': int(L.TOTAL_POP.fillna(0).sum()),
            'age65': int(L.age65.fillna(0).sum()) if rule == 'state' else None,
            'nocar_hh': int(L.nocar.fillna(0).sum()) if rule == 'state' else None,
            'block_groups': [bg.at[i, 'GEOID'] for i in lost],
            'hoods': sorted({h for h in L.hood.dropna()}),
            'lost': detail,
        })

    rows.sort(key=lambda r: r['people'], reverse=True)
    for n, r in enumerate(rows, 1):
        r['rank'] = n
    (DATA / 'cant_lose.json').write_text(json.dumps({'rule': rule, 'stores': rows}, indent=1))

    print(f'{len(rows)} of {len(ph)} pharmacies would push someone into a desert if they closed')
    print(f"{'#':>2}  {'store':22} {'people':>7} {'65+':>6} {'no-car hh':>9}  neighborhoods")
    for r in rows[:TOP]:
        print(f"{r['rank']:>2}  {r['name'][:22]:22} {r['people']:>7} {r['age65'] or 0:>6} "
              f"{r['nocar_hh'] or 0:>9}  {', '.join(r['hoods'])}  ({r['lat']:.4f},{r['lon']:.4f})")


if __name__ == '__main__':
    main()

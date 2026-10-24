# 폐점으로 사막이 된 블록그룹을 되살릴 대체 후보지(보건소·지하철역·점포)를 순위 매기는 스크립트.
import json, math, sys, warnings
from collections import Counter
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from analyze_bg import DATA, MILE, prepare

DESERT_SHARE = 0.15
SEARCH_M = 2 * MILE   # candidates this close to a lost block group
TOP, K = 3, 3         # sites shown, sites in the best set


def candidates():
    s = json.loads((DATA / 'raw' / 'sites.json').read_text())['sites']
    g = gpd.GeoDataFrame(s, geometry=[Point(x['lon'], x['lat']) for x in s], crs=4326).to_crs(26986)
    g['address'] = g['address'].astype(object).where(g['address'].notna(), None)  # NaN breaks JSON
    return g


def score(lost, rest, cands):
    """Per candidate: which lost block groups stop being deserts if a pharmacy opens there."""
    base = {}  # GEOID -> (geometry, radius, union of remaining stores' walk areas, share before)
    for _, b in lost.iterrows():
        near = rest[rest.distance(b.geometry) <= b.radius_m]
        u = unary_union(list(near.geometry.buffer(b.radius_m))) if len(near) else None
        before = b.geometry.intersection(u).area / b.geometry.area if u is not None else 0.0
        base[b['GEOID']] = (b.geometry, b.radius_m, u, before, int(b['TOTAL_POP'] or 0))
    out = []
    reach = cands[cands.geometry.apply(lambda g: lost.distance(g).min() <= SEARCH_M)]
    for _, c in reach.iterrows():
        restored = []
        for g, (geom, r, u, before, pop) in base.items():
            if c.geometry.distance(geom) > r:
                continue
            ring = c.geometry.buffer(r)
            after = geom.intersection(ring if u is None else u.union(ring)).area / geom.area
            if after >= DESERT_SHARE:
                restored.append({'GEOID': g, 'pop': pop, 'share_before': math.floor(before * 1000) / 10,  # floor: 14.96% must not show as 15.0%
                                 'share_after': round(after * 100, 1), 'limit_mi': round(r / MILE, 2)})
        if restored:
            out.append({'name': c['name'], 'kind': c['kind'], 'address': c.get('address'),
                        'lat': c['lat'], 'lon': c['lon'], 'gain': sum(x['pop'] for x in restored),
                        'restored': restored})
    return sorted(out, key=lambda x: -x['gain'])


def best_set(scored, lost_pop):
    """PuLP max-coverage: pick up to K sites that restore the most residents together."""
    try:
        import pulp
    except ImportError:
        return None
    if not scored:
        return {'sites': [], 'gain': 0}
    m = pulp.LpProblem('replacement_sites', pulp.LpMaximize)
    x = {i: pulp.LpVariable(f'x{i}', cat='Binary') for i in range(len(scored))}
    covers = {}
    for i, s in enumerate(scored):
        for r in s['restored']:
            covers.setdefault(r['GEOID'], []).append(i)
    y = {g: pulp.LpVariable(f'y{n}', cat='Binary') for n, g in enumerate(covers)}
    m += pulp.lpSum(lost_pop[g] * y[g] for g in covers)
    m += pulp.lpSum(x.values()) <= K
    for g, sites in covers.items():
        m += y[g] <= pulp.lpSum(x[i] for i in sites)
    m.solve(pulp.PULP_CBC_CMD(msg=False))
    pick = [scored[i]['name'] for i in x if x[i].value() > 0.5]
    return {'sites': pick, 'gain': int(round(pulp.value(m.objective) or 0)), 'solver': 'PuLP CBC'}


def nearest_health_center(lost, cands, scored):
    """Fallback when PuLP is cut: the health center closest to the lost residents' center."""
    hc = cands[cands.kind == 'health_center']
    w = lost.TOTAL_POP.fillna(0)
    pts = lost.geometry.representative_point()
    center = Point((pts.x * w).sum() / w.sum(), (pts.y * w).sum() / w.sum())
    name = hc.loc[hc.distance(center).idxmin(), 'name']
    hit = next((s for s in scored if s['name'] == name), None)
    return {'sites': [name], 'gain': hit['gain'] if hit else 0, 'solver': 'nearest health center'}


def main():
    bg, ph, _, _ = prepare()
    cands = candidates()
    stores = json.loads((DATA / 'cant_lose.json').read_text())['stores']
    out = {}
    for s in stores:
        rest = ph[~((ph.lat == s['lat']) & (ph.lon == s['lon']))]
        lost = bg[bg.GEOID.isin(s['block_groups'])]
        scored = score(lost, rest, cands)
        lost_pop = dict(zip(lost.GEOID, lost.TOTAL_POP.fillna(0).astype(int)))
        best = best_set(scored, lost_pop) or nearest_health_center(lost, cands, scored)
        ring = Counter(round(r / MILE, 2) for r in lost.radius_m).most_common(1)[0][0]
        out[s['rank']] = {'lost_pop': s['people'], 'ring_mi': ring, 'top': scored[:TOP], 'best_set': best}
        top = scored[0] if scored else None
        print(f"#{s['rank']:>2} {s['name'][:22]:22} lost {s['people']:>6}  best site: "
              f"{(top['name'][:34] + ' +' + str(top['gain'])) if top else 'none'}  set of {K}: +{best['gain']}")
    (DATA / 'sites_out.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()

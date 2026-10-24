# 폐점 시 가장 멀어지는 블록그룹에서 다음 약국까지의 실제 도보 경로를 data/routes.json에 저장하는 스크립트.
import json, sys, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import networkx as nx
import osmnx as ox
from pyproj import Transformer
import walk
from analyze_bg import DATA, prepare

TO_LATLON = Transformer.from_crs(26986, 4326, always_xy=True)


def route(G, point, rest):
    """Shortest walk from `point` to the nearest store in `rest` (same search as walk.nearest3)."""
    near = rest.assign(d=rest.distance(point)).nsmallest(walk.CANDIDATES, 'd')
    src = ox.distance.nearest_nodes(G, point.x, point.y)
    dst = ox.distance.nearest_nodes(G, near.geometry.x.values, near.geometry.y.values)
    dist, paths = nx.single_source_dijkstra(G, src, cutoff=walk.CUTOFF_M, weight='length')
    best = min(((dist[n], i) for i, n in enumerate(dst) if n in dist), default=None)
    if best is None:
        return None
    meters, i = best
    store = near.iloc[i]
    coords = []
    for n in paths[dst[i]]:
        lon, lat = TO_LATLON.transform(G.nodes[n]['x'], G.nodes[n]['y'])
        coords.append([round(lat, 6), round(lon, 6)])
    return {'meters': round(meters), 'minutes': round(meters / walk.WALK_MPS / 60),
            'store': store['name'] or 'Pharmacy', 'address': store.get('address'),
            'store_latlon': [store['lat'], store['lon']], 'coords': coords[::2] + coords[-1:]}


def main():
    bg, ph, _, _ = prepare()
    G = walk.graph()
    stores = json.loads((DATA / 'cant_lose.json').read_text())['stores']
    out = {}
    for s in stores:
        far = max((b for b in s['lost'] if b['nearest']), key=lambda b: b['nearest'][0]['walk_m'], default=None)
        if far is None:
            continue
        rest = ph[~((ph.lat == s['lat']) & (ph.lon == s['lon']))]
        p = bg.loc[bg.GEOID == far['GEOID']].geometry.iloc[0].representative_point()
        r = route(G, p, rest)
        if r:
            out[s['rank']] = {'GEOID': far['GEOID'], **r}
            print(f"#{s['rank']:>2} {s['name'][:24]:24} worst block {far['GEOID']}: {r['minutes']} min to {r['store'][:28]}")
    (DATA / 'routes.json').write_text(json.dumps(out))


if __name__ == '__main__':
    main()

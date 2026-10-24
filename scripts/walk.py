# 저장된 보행망으로 블록그룹에서 가장 가까운 약국 3곳까지 걷는 시간을 구하는 모듈.
import pickle
from pathlib import Path
import networkx as nx
import osmnx as ox

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from places import RAW, SLUG, WALK_FILE
DETOUR = 1.3  # street-distance estimate when no walk graph is cached: straight line x 1.3
WALK_MPS = 1.33       # walking speed, m/s
CANDIDATES = 8        # straight-line nearest stores to route to
CUTOFF_M = 8000       # stop searching past 5 miles of walking

_G = None


def graph():
    """Walk graph projected to EPSG:26986, loaded once."""
    global _G
    if _G is None:
        pk = WALK_FILE
        if pk.exists():
            with open(pk, 'rb') as f:
                G = pickle.load(f)
        else:
            G = ox.load_graphml(RAW / 'walk.graphml')
        _G = ox.project_graph(G, to_crs=26986)
    return _G


def has_graph():
    return WALK_FILE.exists() or (SLUG == 'boston' and (RAW / 'walk.graphml').exists())


def nearest3(point, ph):
    """Three nearest stores in `ph` (EPSG:26986 GeoDataFrame) by walking time from `point`."""
    if not has_graph():
        near = ph.assign(d=ph.distance(point)).nsmallest(3, 'd')
        return [{'name': p['name'] or 'Pharmacy', 'address': p.get('address'), 'estimate': True,
                 'walk_m': round(p['d'] * DETOUR), 'walk_min': round(p['d'] * DETOUR / WALK_MPS / 60)}
                for _, p in near.iterrows()]
    G = graph()
    near = ph.assign(d=ph.distance(point)).nsmallest(CANDIDATES, 'd')
    src = ox.distance.nearest_nodes(G, point.x, point.y)
    dst = ox.distance.nearest_nodes(G, near.geometry.x.values, near.geometry.y.values)
    lengths = nx.single_source_dijkstra_path_length(G, src, cutoff=CUTOFF_M, weight='length')
    rows = []
    for (_, p), node in zip(near.iterrows(), dst):
        if node in lengths:
            rows.append({'name': p['name'] or 'Pharmacy', 'address': p.get('address'),
                         'walk_m': round(lengths[node]), 'walk_min': round(lengths[node] / WALK_MPS / 60)})
    return sorted(rows, key=lambda r: r['walk_m'])[:3]

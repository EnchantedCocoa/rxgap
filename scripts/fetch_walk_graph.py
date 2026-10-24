# 보스턴 경계 +1마일 보행 네트워크(OSM)를 받아 graphml로 저장하는 스크립트.
import json, time, sys, warnings
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings('ignore')
import geopandas as gpd
from shapely.ops import unary_union
import osmnx as ox

ROOT = Path(__file__).resolve().parent.parent
BG = ROOT / 'data' / 'raw' / 'boston_bg.geojson'
OUT = ROOT / 'data' / 'raw' / 'walk.graphml'
META = ROOT / 'data' / 'raw' / 'walk.meta.json'

MILE_M = 1609.344  # 1 mile in meters
WORK_CRS = 'EPSG:26986'  # MA state plane, meters


def boundary_polygon():
    # 블록그룹 합집합을 EPSG:26986에서 1마일 버퍼 후 4326으로 되돌린 경계.
    g = gpd.read_file(BG)
    poly_m = unary_union(g.to_crs(WORK_CRS).geometry.values).buffer(MILE_M)
    return gpd.GeoSeries([poly_m], crs=WORK_CRS).to_crs('EPSG:4326').iloc[0]


def fetch_graph(poly, tries=5):
    # Overpass는 502를 자주 반환 -> 지수 백오프 재시도.
    delay = 5
    for i in range(tries):
        try:
            return ox.graph_from_polygon(poly, network_type='walk')
        except Exception as e:
            msg = str(e)[:140]
            print(f'  retry {i+1}/{tries} after {delay}s ({msg})', file=sys.stderr)
            if i == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError('unreachable')


def main():
    poly = boundary_polygon()
    print(f'boundary bounds (4326): {poly.bounds}')
    print('downloading walk network via Overpass...', file=sys.stderr)
    G = fetch_graph(poly)
    n, m = G.number_of_nodes(), G.number_of_edges()
    print(f'graph: {n} nodes, {m} edges')
    ox.save_graphml(G, OUT)
    meta = {
        'dataset': 'OpenStreetMap walk network, Boston + 1 mi',
        'source': 'Overpass via osmnx',
        'function': 'scripts/fetch_walk_graph.py:main',
        'pulled': datetime.now(timezone.utc).isoformat(),
        'nodes': n,
        'edges': m,
    }
    META.write_text(json.dumps(meta, indent=2))
    print(f'wrote {OUT} and {META}')
    return G


if __name__ == '__main__':
    main()

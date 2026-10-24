# 보스턴 외 도시(스프링필드·플리머스)의 주 정부(HPC) 블록그룹 판정을 지도용 파일로 만드는 스크립트.
import json, re, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
HPC = ROOT / 'data' / 'raw' / 'hpc'
OUT = ROOT / 'data' / 'towns'
STATUS = {'Pharmacy deserts': 'desert', 'Near deserts': 'near-desert', 'Non-deserts': 'covered'}
LIMIT_MI = {'urban': 1.0, 'suburban': 2.0, 'rural': 5.0}  # halved for low-access (HPC DataPoints 31)
TOWNS = {
    'springfield': {'name': 'Springfield', 'why': 'Most residents at risk of any large Massachusetts city'},
    'plymouth': {'name': 'Plymouth', 'why': 'Most residents at risk of any mostly-suburban town'},
}


def main():
    OUT.mkdir(exist_ok=True)
    hpc = pd.read_csv(HPC / 'hpc_bg_with_town.csv', dtype={'GEOID': str})
    shapes = gpd.read_file(f'zip://{HPC / "bg.zip"}')[['GEOID', 'geometry']]
    summary = {}
    for slug, t in TOWNS.items():
        d = hpc[hpc.town == t['name']].copy()
        lvl = d['Geographic level (HPC)'].str.lower()
        d['type'] = lvl.str.extract('(urban|suburban|rural)')[0]
        d['low_access'] = lvl.str.startswith('low')
        d['limit_mi'] = [LIMIT_MI[k] / (2 if low else 1) for k, low in zip(d['type'], d['low_access'])]
        g = shapes.merge(d, on='GEOID').to_crs(26986)
        g['geometry'] = g.geometry.simplify(10)
        props = pd.DataFrame({
            'GEOID': g.GEOID, 'pop': g.POP20.astype(int), 's_state': g['Category (HPC)'].map(STATUS),
            'type': g['type'], 'low_access': g['low_access'], 'limit_mi': g['limit_mi'],
            'share_in_reach': (g['Share of block group within pharmacy radius (HPC)'] * 100).round(1),
            'nocar_pct': (g['Share of households without a vehicle'] * 100).round(1),
            'pov_pct': (g['Share of households below the FPL'] * 100).round(1),
            'age65_pct': (g['Share of population above age 65'] * 100).round(1),
            'stores_near': g['Retail pharmacy count'].astype(int)})
        out = gpd.GeoDataFrame(props, geometry=g.geometry, crs=26986).to_crs(4326)
        out.to_file(OUT / f'{slug}.geojson', driver='GeoJSON')
        n = lambda s: int(props.loc[props.s_state == s, 'pop'].sum())
        types = props.groupby('type')['pop'].sum().astype(int).to_dict()
        b = out.total_bounds
        summary[slug] = {**t, 'desert': n('desert'), 'near': n('near-desert'), 'covered': n('covered'),
                         'total': int(props['pop'].sum()), 'blocks': len(props), 'types': types,
                         'bounds': [[b[1], b[0]], [b[3], b[2]]]}
        print(f"{t['name']}: {len(props)} block groups, desert {n('desert')}, near {n('near-desert')}, types {types}")
    (OUT / 'towns.json').write_text(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()

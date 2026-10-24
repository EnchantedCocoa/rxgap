# 선택한 장소의 모든 2020 블록그룹(인구조사 TIGER)과 인구·면적·제한적 영어·소득·ACS를 받아 저장하는 스크립트.
import csv, io, json, sys, warnings, zipfile
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import requests
from analyze_bg import census_key, fetch_acs
from places import BG_FILE, PLACE

RAW = Path(__file__).resolve().parent.parent / 'data' / 'raw'
TIGER = 'https://www2.census.gov/geo/tiger/GENZ2020/shp/'
LIMENG = ['C16002_004E', 'C16002_007E', 'C16002_010E', 'C16002_013E']  # limited-English households


def tiger(name):
    p = RAW / 'hpc' / f'{name}.zip'
    if not p.exists():
        p.parent.mkdir(exist_ok=True)
        p.write_bytes(requests.get(TIGER + f'cb_2020_25_{name}_500k.zip', timeout=120).content)
    return gpd.read_file(f'zip://{p}')


def census(url, get):
    rows = requests.get(url, params={'get': ','.join(get), 'for': 'block group:*',
                                     'in': f"state:25 county:{PLACE['county']}", 'key': census_key()}, timeout=60).json()
    head = rows[0]
    out = {}
    for r in rows[1:]:
        d = dict(zip(head, r))
        out[d['state'] + d['county'] + d['tract'] + d['block group']] = {k: int(d[k]) for k in get}
    return out


def main():
    bg = tiger('bg').to_crs(26986)
    towns = tiger('cousub').to_crs(26986)
    town = towns[towns.NAME == PLACE['name']].geometry.iloc[0]
    bg = bg[bg.representative_point().within(town)][['GEOID', 'ALAND', 'geometry']].copy()
    # Rural flag: the HPC dataset carries the State Office of Rural Health designation per block group.
    hpc = {r['GEOID']: r for r in csv.DictReader(open(RAW / 'hpc' / 'hpc_bg_with_town.csv'))}
    bg['RURAL'] = bg.GEOID.map(lambda g: hpc.get(g, {}).get('Rurality') == 'Rural')

    pop = census('https://api.census.gov/data/2020/dec/pl', ['P1_001N'])
    acs = census('https://api.census.gov/data/2022/acs/acs5', ['C16002_001E', 'B19013_001E'] + LIMENG)
    bg['TOTAL_POP'] = bg.GEOID.map(lambda g: pop.get(g, {}).get('P1_001N', 0))
    bg['TOTALHH'] = bg.GEOID.map(lambda g: acs.get(g, {}).get('C16002_001E', 0))
    bg['LIMENGHHPCT'] = [round(sum(acs[g][k] for k in LIMENG) / acs[g]['C16002_001E'] * 100, 1)
                         if acs.get(g, {}).get('C16002_001E') else 0.0 for g in bg.GEOID]
    bg['BG_MHHI'] = bg.GEOID.map(lambda g: max(acs.get(g, {}).get('B19013_001E', 0), 0))  # -666666666 = no estimate

    # State-wide car ownership, the benchmark the HPC compares each block group to.
    s = requests.get('https://api.census.gov/data/2022/acs/acs5',
                     params={'get': 'B25044_001E,B25044_003E,B25044_010E', 'for': 'state:25', 'key': census_key()},
                     timeout=60).json()[1]
    (RAW / 'acs_state.json').write_text(json.dumps({'nocar_share': (int(s[1]) + int(s[2])) / int(s[0]),
                                                    'source': 'ACS 2022 5-year B25044, Massachusetts'}))
    bg.to_crs(4326).to_file(BG_FILE, driver='GeoJSON')
    fetch_acs(census_key())
    print(f"{len(bg)} {PLACE['name']} block groups, {bg.TOTAL_POP.sum()} people -> {BG_FILE.name}")


if __name__ == '__main__':
    main()

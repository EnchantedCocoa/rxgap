# 블록그룹마다 시의회·주 하원·주 상원 선거구를 정해 data/bg_districts.json에 저장하는 스크립트.
import json, sys, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
from fetch_districts import assign_by_area, council_id, house_id, senate_id
from places import BG_FILE, OUT as PLACE_OUT, PLACE

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
OUT = PLACE_OUT / 'bg_districts.json'


def main():
    bg = gpd.read_file(BG_FILE)
    out = {g: {} for g in bg['GEOID']}
    kinds = [('council', council_id)] if PLACE['council'] else []
    for kind, fn in kinds + [('house', house_id), ('senate', senate_id)]:
        d = gpd.read_file(RAW / f'{kind}.geojson')
        assign = assign_by_area(bg, d, fn, kind)[0]
        for g, v in assign.items():
            out[g][kind] = str(v)
    OUT.write_text(json.dumps(out, indent=0))
    print(f'wrote districts for {len(out)} block groups -> {OUT}')


if __name__ == '__main__':
    main()

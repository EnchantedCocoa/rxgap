# 원본 데이터만으로 사막·준사막·충족 인구를 다시 계산해 화면 숫자와 비교하는 스크립트.
import json, sys, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_bg import DATA, prepare, status_at


def main():
    bg, ph, _, rule = prepare()  # reads data/raw/ and data/manual/ only
    fresh = {'desert': 0, 'near-desert': 0, 'covered': 0}
    for _, b in bg.iterrows():
        fresh[status_at(b.geometry, ph, b.radius_m)[1]] += int(b['TOTAL_POP'] or 0)

    shown = {k: 0 for k in fresh}
    for f in json.loads((DATA / 'bg_out.geojson').read_text())['features']:
        shown[f['properties']['s_state']] += f['properties']['pop']

    print(f'rule: {rule}')
    ok = True
    for k in fresh:
        mark = 'ok' if fresh[k] == shown[k] else 'MISMATCH'
        ok &= fresh[k] == shown[k]
        print(f'{k:12s} recomputed {fresh[k]:7d}   on screen {shown[k]:7d}   {mark}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

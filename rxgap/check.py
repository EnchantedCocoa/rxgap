# closures.csv 기준으로 재계산하고 상태가 바뀐 블록그룹만 출력하는 매일 점검 명령.
import io, json, sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_bg, rank  # noqa: E402

SNAP = ROOT / 'data' / 'last_status.json'


def main():
    with redirect_stdout(io.StringIO()):  # keep output to the change summary only
        analyze_bg.main()
        rank.main()
    feats = json.loads((ROOT / 'data' / 'bg_out.geojson').read_text())['features']
    now = {f['properties']['GEOID']: f['properties'] for f in feats}
    if not SNAP.exists():
        SNAP.write_text(json.dumps({g: p['s_state'] for g, p in now.items()}))
        print(f'baseline saved for {len(now)} block groups')
        return
    old = json.loads(SNAP.read_text())
    changed = [g for g, p in now.items() if old.get(g) != p['s_state']]
    for g in changed:
        p = now[g]
        print(f"{g} {p.get('hood') or ''}: {old.get(g, 'new')} -> {p['s_state']}, "
              f"{p['pop']} people, council {p.get('council', '?')}, "
              f"{p.get('house', '?')}, {p.get('senate', '?')}")
    if changed:
        print(f'{len(changed)} block groups changed, '
              f"{sum(now[g]['pop'] for g in changed)} people")
    SNAP.write_text(json.dumps({g: p['s_state'] for g, p in now.items()}))


if __name__ == '__main__':
    main()

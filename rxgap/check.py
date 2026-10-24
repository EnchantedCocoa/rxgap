# closures.csv를 반영해 세 장소 파이프라인 전체를 다시 돌리고, 상태가 바뀐 블록그룹만 출력하는 매일 점검 명령.
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACES = {'boston': ROOT / 'data', 'springfield': ROOT / 'data' / 'places' / 'springfield',
          'plymouth': ROOT / 'data' / 'places' / 'plymouth'}


def statuses(base):
    return {f['properties']['GEOID']: f['properties']
            for f in json.loads((base / 'bg_out.geojson').read_text())['features']}


def main(places=None):
    """Rerun every step (run_all.py), then compare each place with yesterday's snapshot.

    Prints one line per changed block group and a total per place, or exactly 'no change'.
    """
    places = places or list(PLACES)
    r = subprocess.run([sys.executable, 'scripts/run_all.py', *places], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'pipeline failed:\n{(r.stderr or r.stdout)[-2000:]}')
    lines = []
    for slug in places:
        base, name = PLACES[slug], slug.title()
        now = statuses(base)
        snap = base / 'last_status.json'
        old = json.loads(snap.read_text()) if snap.exists() else None
        snap.write_text(json.dumps({g: p['s_state'] for g, p in now.items()}))
        if old is None:
            lines.append(f'{name}: baseline saved for {len(now)} block groups')
            continue
        changed = [g for g, p in now.items() if old.get(g) != p['s_state']]
        for g in changed:
            p = now[g]
            where = ', '.join(x for x in [p.get('hood'), p.get('council') and f"council {p['council']}", p.get('house'), p.get('senate')] if x)
            lines.append(f"{name} {g} ({where}): {old.get(g, 'new')} -> {p['s_state']}, {p['pop']} people")
        if changed:
            lines.append(f"{name}: {len(changed)} block groups changed, {sum(now[g]['pop'] for g in changed)} people")
    print('\n'.join(lines) if lines else 'no change')


if __name__ == '__main__':
    main(sys.argv[1:])

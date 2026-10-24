# 세 장소 모두 분석 파이프라인을 순서대로 다시 돌리는 실행 스크립트 (python scripts/run_all.py [place ...]).
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = ['route.py', 'analyze_bg.py', 'rank.py', 'siting.py', 'routes.py', 'build_app_data.py', 'build_facts.py']


def main():
    places = sys.argv[1:] or ['boston', 'springfield', 'plymouth']
    subprocess.run([sys.executable, 'scripts/build_provenance.py'], cwd=ROOT, check=True)
    for place in places:
        env = {**os.environ, 'RXGAP_PLACE': place}
        for step in STEPS:
            r = subprocess.run([sys.executable, f'scripts/{step}'], cwd=ROOT, env=env, capture_output=True, text=True)
            if r.returncode:
                sys.exit(f'{place} {step} failed:\n{r.stderr[-2000:]}')
            lines = [l for l in r.stdout.splitlines() if not l.startswith(('closure ', 'opening '))]
            print(f'[{place}] {step}: ' + (lines[-1] if lines else 'ok'))


if __name__ == '__main__':
    main()

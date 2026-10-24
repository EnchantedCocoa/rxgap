# 제출용 글(docs/SUBMISSION.md)을 숫자 없는 템플릿에 분석 결과·근거 파일의 숫자를 넣어 만드는 스크립트.
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rxgap.text import render  # noqa: E402

PLACES = {'boston': ROOT / 'data', 'springfield': ROOT / 'data' / 'places' / 'springfield',
          'plymouth': ROOT / 'data' / 'places' / 'plymouth'}
TEMPLATE = ROOT / 'docs' / 'submission.template.md'
OUT = ROOT / 'docs' / 'SUBMISSION.md'


def load(p):
    return json.loads(Path(p).read_text())


def facts():
    E = {e['id']: e for e in load(ROOT / 'data' / 'manual' / 'evidence.json')}
    K = {k: v['value'] for k, v in load(ROOT / 'docs' / 'kiro_facts.json').items() if not k.startswith('_')}
    boston = load(PLACES['boston'] / 'facts.json')['place']
    places = []
    for slug, base in PLACES.items():
        D = load(base / 'app_data.json')
        h, v, s = D['headline']['state'], D['validation'], D['stores'][0]
        places.append({'name': D['place']['name'], 'desert': h['desert'], 'near': h['near'], 'one_in': f"1 in {v['one_in']}",
                       'hpc_agree': v['hpc_agree'], 'top_name': s['name'], 'top_street': s['address'].split(',')[0],
                       'top_people': s['people']})
    langs = sorted({p.name.split('.')[1] for p in (ROOT / 'data' / 'templates').glob('letter.*.md')})
    names = [p['name'] for p in places]
    return {**K, 'places': places, 'place_names': ', '.join(names[:-1]) + ' and ' + names[-1],
            'lang_count': len(langs), 'hpc_report': boston['hpc_report'],
            'state_desert': E['ma-pharmacy-deserts']['value'],
            'state_source': f"{E['ma-pharmacy-deserts']['publisher']}, {E['ma-pharmacy-deserts']['year']}",
            'qato_source': f"Qato et al., JAMA Network Open, {E['qato-statin-drop']['year']}",
            'pickup_rides_cite': boston['pickup_rides_cite'], 'closure_notice_days': boston['closure_notice_days'],
            'petition_days': next(r['value'] for r in load(ROOT / 'data' / 'manual' / 'policy.json') if r['id'] == 'boston_petition')}


def build():
    return render(TEMPLATE.read_text(), facts())


if __name__ == '__main__':
    OUT.write_text(build())
    print(f'wrote {OUT.relative_to(ROOT)}')

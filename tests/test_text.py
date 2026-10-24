# 브리프·편지·배달 도우미의 모든 숫자가 사실(facts)에서 왔고, 그 사실이 분석 결과와 같은지 확인하는 테스트.
import html, json, re
from pathlib import Path
import pytest
from rxgap.text import fmt, numbers, render

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / 'data' / 'templates'
BASES = {'boston': ROOT / 'data', 'springfield': ROOT / 'data' / 'places' / 'springfield',
         'plymouth': ROOT / 'data' / 'places' / 'plymouth'}
LANGS = ['en', 'es', 'ht']
SENTENCE = 'My mother takes her heart medicine every day.'
POLICY = {r['id']: r for r in json.loads((ROOT / 'data' / 'manual' / 'policy.json').read_text())}


def load(p):
    return json.loads(p.read_text())


def values(x):
    """Every printable fact value, as it would be printed."""
    if isinstance(x, dict):
        for v in x.values():
            yield from values(v)
    elif isinstance(x, list):
        for v in x:
            yield from values(v)
    elif x is not None and not isinstance(x, bool):
        yield fmt(x)


def text_of(out):
    """Visible text only: tag names like h2 and entities like &#39; are not numbers."""
    return html.unescape(re.sub(r'<[^>]+>', ' ', out))


def only_fact_numbers(out, facts):
    out = text_of(out)
    allowed = set().union(*(numbers(v) for v in values(facts)))
    assert numbers(out) <= allowed, numbers(out) - allowed


def test_templates_have_no_digits():
    names = [p.name for p in TPL.iterdir() if p.name.startswith(('brief', 'letter', 'help'))]
    assert len(names) == 10
    for n in names:
        prose = re.sub(r'\{[#?^/]?\w+\}', '', text_of((TPL / n).read_text()))  # placeholder names may hold digits
        assert not re.search(r'\d', prose), n


def test_policy_rows_have_sources():
    for r in POLICY.values():
        assert r['url'].startswith('https://') and r['statement'], r['id']
        assert re.fullmatch(r'\d{4}-\d\d-\d\d', r['confirmed']), r['id']


@pytest.mark.parametrize('slug', BASES)
def test_letters_and_help_print_only_fact_numbers(slug):
    F = load(BASES[slug] / 'facts.json')
    for b in F['blocks'].values():
        facts = {**F['place'], **b, 'own_sentence': SENTENCE}
        for kind in ('letter', 'letter_masshealth', 'help'):
            if kind == 'letter' and not (b['is_near'] or b['is_desert']):
                continue  # covered blocks have no letter to their officials
            for lang in LANGS:
                out = render((TPL / f'{kind}.{lang}.md').read_text(), facts)
                only_fact_numbers(out, facts)
                if kind != 'help':
                    assert SENTENCE in out and 'Hackachusetts' in out and b['officials_line'] in out


@pytest.mark.parametrize('slug', BASES)
def test_briefs_print_only_fact_numbers(slug):
    F = load(BASES[slug] / 'facts.json')
    tpl = (TPL / 'brief.en.html').read_text()
    for rows in F['briefs'].values():
        for r in rows:
            facts = {**F['place'], **r, 'letters': 0}
            out = render(tpl, facts, html=True)
            only_fact_numbers(out, facts)
            assert out.count('<tr>') == 1 + len(r['blocks']) + (1 + len(r['sites']) if r['sites'] else 0)


@pytest.mark.parametrize('slug', BASES)
def test_facts_match_analysis(slug):
    base = BASES[slug]
    F = load(base / 'facts.json')
    stores = {str(s['rank']): s for s in load(base / 'cant_lose.json')['stores']}
    sites = load(base / 'sites_out.json')
    bg = {f['properties']['GEOID']: f['properties'] for f in load(base / 'bg_out.geojson')['features']}
    extras = load(base / 'block_extras.json')
    pl = F['place']
    assert pl['place_desert'] == sum(p['pop'] for p in bg.values() if p['s_state'] == 'desert')
    assert pl['place_near'] == sum(p['pop'] for p in bg.values() if p['s_state'] == 'near-desert')
    for key, pid in [('closure_notice_days', 'closure_notice'), ('delivery_fee', 'delivery_fee'),
                     ('mail_months', 'mail_months'), ('pt1_days', 'pt1_days')]:
        assert pl[key] == POLICY[pid]['value'], key
    assert pl['pickup_rides_cite'] == POLICY['pickup_rides']['cite']

    for rank, rows in F['briefs'].items():
        s = stores[rank]
        assert rows, rank
        for r in rows:
            assert (r['store_people'], r['store_age65'], r['store_nocar_hh']) == (s['people'], s['age65'], s['nocar_hh'])
            kind, did = r['official_key'].split(':', 1)
            mine = [b for b in s['lost'] if b['districts'].get(kind) == did]
            assert r['official_people'] == sum(b['pop'] for b in mine)
            assert [(x['geoid'], x['pop'], x.get('near_min')) for x in r['blocks']] == \
                [(b['GEOID'], b['pop'], b['nearest'][0]['walk_min'] if b['nearest'] else None) for b in mine]
            assert [x['gain'] for x in r['sites']] == [x['gain'] for x in sites[rank]['top']]
        assert sum(r['official_people'] for r in rows if r['official_key'].startswith('house:')) == s['people']

    for g, b in F['blocks'].items():
        p = bg[g]
        assert (b['block_pop'], b['is_desert'], b['is_near']) == (p['pop'], p['s_state'] == 'desert', p['s_state'] == 'near-desert')
        if b['is_near']:
            s = min((s for s in stores.values() if g in s['block_groups']), key=lambda s: s['rank'])
            assert (b['store_people'], b['store_age65'], b['store_nocar_hh']) == (s['people'], s['age65'], s['nocar_hh'])
            top = sites[str(s['rank'])]['top']
            assert b.get('site_gain') == (top[0]['gain'] if top else None)
        elif b['is_desert']:
            assert b.get('site_gain') == extras[g].get('site', {}).get('gain')
        else:
            assert 'store_people' not in b and 'site_gain' not in b
        assert [n['mi'] for n in b['near_stores']] == [n['mi'] for n in extras[g]['near']]

# 헤드리스 브라우저로 1위 약국 폐점을 눌러 결과 카드 숫자가 분석 결과와 같은지 보는 UI 테스트.
import json, os, socket, subprocess, sys, time
from pathlib import Path
import pytest

pw = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parent.parent
SHOTS = Path(os.environ.get('KIROCREW_SCRATCH', ROOT / '.pytest_cache'))


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def page():
    port = free_port()
    db = SHOTS / f'letters_test_{port}.duckdb'
    srv = subprocess.Popen([sys.executable, '-m', 'rxgap.serve', str(port)], cwd=ROOT,
                           env={**os.environ, 'RXGAP_DB': str(db)},
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    with pw.sync_playwright() as p:
        try:  # real Chrome, like the demo laptop; headless it has no WebGL, which the app must not need
            b = p.chromium.launch(channel='chrome')
        except Exception:
            b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(f'http://127.0.0.1:{port}/app/?tour=0&splash=0')
        pg.wait_for_function('window.rxgap !== undefined', timeout=30000)
        pg.errors = errors
        yield pg
        b.close()
    srv.terminate()
    srv.wait()
    db.unlink(missing_ok=True)


def test_server_blocks_secrets(page):
    r = page.request.get(page.url.replace('/app/', '/.env'))
    assert r.status == 404


def test_close_top_store_matches_analysis(page):
    top = json.loads((ROOT / 'data' / 'cant_lose.json').read_text())['stores'][0]
    page.screenshot(path=str(SHOTS / 'ui_before.png'))
    page.click('.rank-row[data-rank="1"]')
    page.click('#simulate')
    page.wait_for_timeout(1600)
    page.screenshot(path=str(SHOTS / 'ui_after.png'))
    assert page.inner_text('#r-people') == f"{top['people']:,}"
    assert page.inner_text('#r-65') == f"{top['age65']:,}"
    assert [e for e in page.errors if 'arcgisonline' not in e] == []


def test_map_draws_every_block_group(page):
    n_bg = len(json.loads((ROOT / 'data' / 'bg_out.geojson').read_text())['features'])
    assert page.locator('path.bg').count() == n_bg == 580
    n = len(json.loads((ROOT / 'data' / 'cant_lose.json').read_text())['stores'])
    assert page.locator('.pin-rank').count() == n


def test_undo_restores(page):
    page.click('#undo2')
    assert page.is_hidden('#result-card')


def test_siting_view_matches_analysis(page):
    sites = json.loads((ROOT / 'data' / 'sites_out.json').read_text())['1']
    page.click('#simulate')
    page.wait_for_timeout(900)
    page.click('#sites-btn')
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SHOTS / 'ui_sites.png'))
    assert page.inner_text('#r-best') == f"{sites['best_set']['gain']:,}"
    assert page.locator('.pin-site').count() == len(sites['top'])
    assert page.locator('path.is-restored').count() == len(sites['top'][0]['restored'])


def test_letter_counts_endpoint(page):
    base = page.url.split('/app/')[0]
    assert page.request.post(f'{base}/count', data={'district_type': 'council', 'district_id': '7'}).ok
    assert page.request.post(f'{base}/count', data={'district_type': 'council', 'district_id': 'x'}).status == 400
    rows = page.request.get(f'{base}/counts').json()
    assert any(r['district_type'] == 'council' and r['district_id'] == '7' and r['letters'] >= 1 for r in rows)
    assert set(rows[0]) == {'district_type', 'district_id', 'letters'}  # no names or addresses


def test_place_picker_loads_full_places(page):
    for slug in ['springfield', 'plymouth']:
        app = json.loads((ROOT / 'data' / 'places' / slug / 'app_data.json').read_text())
        page.select_option('#town', slug)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SHOTS / f'ui_{slug}.png'))
        h = app['headline']['state']
        assert page.inner_text('[data-num="desert"]') == f"{h['desert']:,}"
        assert page.locator('path.bg').count() == len(json.loads((ROOT / 'data' / 'places' / slug / 'bg_out.geojson').read_text())['features'])
        assert page.locator('.rank-row').count() == len(app['stores'])
        page.click('.rank-row[data-rank="1"]')
        page.click('#simulate')
        page.wait_for_timeout(1500)
        assert page.inner_text('#r-people') == f"{app['stores'][0]['people']:,}"
        page.screenshot(path=str(SHOTS / f'ui_{slug}_closure.png'))
        page.click('#undo2')
    page.select_option('#town', 'boston')
    page.wait_for_timeout(1500)
    app = json.loads((ROOT / 'data' / 'app_data.json').read_text())
    assert page.inner_text('[data-num="desert"]') == f"{app['headline']['state']['desert']:,}"
    assert page.locator('path.bg').count() == 580


def test_switch_place_during_closure_has_no_errors(page):
    page.errors.clear()
    page.click('.rank-row[data-rank="1"]')
    page.click('#simulate')
    page.wait_for_timeout(1500)
    page.select_option('#town', 'springfield')  # undo's wave must not touch the new map
    page.wait_for_timeout(2000)
    assert [e for e in page.errors if 'arcgisonline' not in e] == []
    page.select_option('#town', 'boston')
    page.wait_for_timeout(1500)


def test_closure_draws_walking_route(page):
    top = json.loads((ROOT / 'data' / 'app_data.json').read_text())['stores'][0]
    page.select_option('#town', 'boston')
    page.wait_for_timeout(800)
    page.click('.rank-row[data-rank="1"]')
    page.click('#simulate')
    page.wait_for_timeout(3800)
    page.screenshot(path=str(SHOTS / 'ui_route.png'))
    assert page.locator('path.route').count() == 1
    assert page.inner_text('.route-tag').startswith(f"{top['route']['minutes']} min walk")
    page.click('#undo2')
    assert page.locator('path.route').count() == 0


def test_tour_uses_code_numbers(page):
    app = json.loads((ROOT / 'data' / 'app_data.json').read_text())
    page.click('#play-tour')
    page.wait_for_timeout(500)
    assert f"1 in {app['validation']['one_in']}" in page.inner_text('#tour-text')
    page.click('#tour-next')
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SHOTS / 'ui_tour.png'))
    assert f"{app['stores'][0]['people']:,}" in page.inner_text('#tour-text')
    page.click('#tour-skip')
    assert page.is_hidden('#tour')


def test_story_numbers_come_from_data(page):
    app = json.loads((ROOT / 'data' / 'app_data.json').read_text())
    ev = {f['id']: f for f in json.loads((ROOT / 'data' / 'manual' / 'evidence.json').read_text())}
    page.goto(page.url.split('?')[0] + '?tour=0')
    page.wait_for_selector('#essay .es-ch')
    page.screenshot(path=str(SHOTS / 'ui_story.png'))
    vals = [' '.join(v.split()) for v in page.locator('#essay .es-val').all_inner_texts()]
    h = app['headline']['state']
    assert f"{h['desert'] + h['near']:,}" in [v.rstrip('i').strip() for v in vals]
    assert page.inner_text('#essay .es-num') == f"{app['stores'][0]['people']:,}"
    shown = {v.rstrip('i').strip() for v in vals}
    assert shown - {f['value'] for f in ev.values()} == {f"{h['desert'] + h['near']:,}"}
    assert page.locator('#essay .es-src').count() == page.locator('#essay .es-val').count()  # every number names its source
    assert page.locator('#essay .es-credit').count() == len(json.loads((ROOT / 'data' / 'manual' / 'photos.json').read_text())) == 5
    page.click('#es-skip')
    page.wait_for_selector('#essay', state='detached')
    assert [e for e in page.errors if 'arcgisonline' not in e] == []


def test_story_one_arrow_press_moves_one_scene(page):
    page.goto(page.url.split('?')[0] + '?tour=0')
    page.wait_for_selector('#essay .es-ch')
    spot = """i => { const r = document.querySelector('#essay'), s = r.querySelectorAll('.es-ch')[i];
      return Math.max(0, Math.min(r.scrollHeight - r.clientHeight, s.offsetTop + (s.offsetHeight - r.clientHeight) / 2)); }"""
    top = lambda: page.evaluate("document.querySelector('#essay').scrollTop")
    page.keyboard.press('ArrowDown')
    page.wait_for_timeout(1700)
    assert abs(top() - page.evaluate(spot, 1)) < 2
    page.keyboard.press('ArrowDown')
    page.keyboard.press('ArrowDown')  # a quick second press queues the next scene
    page.wait_for_timeout(1700)
    assert abs(top() - page.evaluate(spot, 3)) < 2
    page.keyboard.press('ArrowUp')
    page.wait_for_timeout(1700)
    assert abs(top() - page.evaluate(spot, 2)) < 2
    assert [e for e in page.errors if 'arcgisonline' not in e] == []


def test_browser_renders_text_like_python(page):
    from rxgap.text import render
    F = json.loads((ROOT / 'data' / 'facts.json').read_text())
    picks = [next(b for b in F['blocks'].values() if b['is_near']),
             next(b for b in F['blocks'].values() if b['is_desert'] and 'site_name' in b),
             next(b for b in F['blocks'].values() if not (b['is_near'] or b['is_desert']))]
    cases = [(f'{k}.{l}.md', {**F['place'], **b, 'own_sentence': "It's far & I'm <tired>."}, False)
             for b in picks for k in ('letter', 'letter_masshealth', 'help') for l in ('en', 'es', 'ht')
             if k != 'letter' or b['is_near'] or b['is_desert']]
    cases += [('brief.en.html', {**F['place'], **r, 'letters': 3}, True) for r in F['briefs']['1']]
    for name, facts, html in cases:
        tpl = (ROOT / 'data' / 'templates' / name).read_text()
        js = page.evaluate("async ([t, f, h]) => (await import('/app/text.js')).render(t, f, h)", [tpl, facts, html])
        assert js == render(tpl, facts, html), name


def facts():
    return json.loads((ROOT / 'data' / 'facts.json').read_text())


def fresh(page):
    page.goto(page.url.split('?')[0] + '?tour=0&splash=0')
    page.wait_for_function('window.rxgap !== undefined', timeout=30000)


def test_brief_shows_fact_numbers(page):
    F = facts()
    fresh(page)
    page.evaluate('window.rxgap.simulate(1)')
    page.click('#brief-btn')
    page.wait_for_selector('#act .brief')
    r = F['briefs']['1'][0]
    assert page.inner_text('#act .brief-lead b') == f"{r['official_people']:,}"
    assert page.locator('#act .brief tbody tr').count() == len(r['blocks']) + len(r['sites'])
    page.select_option('#brief-who', F['briefs']['1'][-1]['official_key'])
    page.wait_for_function(f"document.querySelector('#act .brief-for').textContent.includes({json.dumps(F['briefs']['1'][-1]['official_name'])})")
    page.click('#act .close')
    page.evaluate('window.rxgap.undo()')


def test_delivery_helper_has_no_inputs_and_sends_nothing(page):
    F = facts()
    fresh(page)
    sent = []
    spy = lambda r: sent.append((r.method, r.url))
    page.on('request', spy)
    g = next(g for g, b in F['blocks'].items() if b['is_near'])
    page.evaluate(f'window.rxgap.sheet({json.dumps(g)})')
    page.click('#sheet-help')
    page.wait_for_selector('#act .act-src')
    for lang in ('es', 'ht', 'en'):
        page.click(f'#act [data-lang="{lang}"]')
        page.wait_for_function(f"document.querySelector('#act .act-body').lang === '{lang}'")
        assert F['blocks'][g]['near_stores'][0]['name'] in page.inner_text('#act .act-body')
    assert page.locator('#act input, #act textarea, #act select').count() == 0
    assert all(m == 'GET' and '?' not in u for m, u in sent), sent  # nothing about the page leaves the browser
    page.remove_listener('request', spy)
    page.click('#act .close')


def test_letter_flow_needs_own_words_counts_and_never_sends(page):
    F = facts()
    g = next(g for g, b in F['blocks'].items() if b['is_near'])
    b = F['blocks'][g]
    fresh(page)
    posts = []
    spy = lambda r: r.method == 'POST' and posts.append(r.url)
    page.on('request', spy)
    page.evaluate(f'window.rxgap.sheet({json.dumps(g)})')
    page.click('#sheet-letter')
    page.wait_for_selector('#ok1')
    page.click('#ok1')
    assert page.is_disabled('#make')
    page.click('#act [data-lang="ht"]')
    page.fill('#own', 'Manman m pran medikaman pou kè chak jou.')
    page.click('#make')
    page.wait_for_selector('#act .letters.two')
    texts = page.locator('#act .letter-text').all_inner_texts()
    assert all(f"{b['store_people']:,}" in t and 'Manman m pran' in t for t in texts)
    page.click('#back3')
    page.click('#make')  # same letter again: counted once
    page.wait_for_selector('#act .letters')
    page.wait_for_timeout(300)
    assert len(posts) == len(b['officials']) and all(u.endswith('/count') for u in posts)
    assert page.locator('#act a[href^="mailto:?subject="]').count() == 1  # the resident opens their own email
    page.click('#act .close')
    page.remove_listener('request', spy)
    assert [e for e in page.errors if 'arcgisonline' not in e] == []
    assert page.evaluate("fetch('/geocode?address=ab').then(r => r.status)") == 400  # too short: never sent on

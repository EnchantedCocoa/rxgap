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

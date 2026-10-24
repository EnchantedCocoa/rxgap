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
        pg.goto(f'http://127.0.0.1:{port}/app/')
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
    assert page.locator('path.bg').count() == 462
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

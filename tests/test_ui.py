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
    srv = subprocess.Popen([sys.executable, '-m', 'rxgap.serve', str(port)], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    with pw.sync_playwright() as p:
        b = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
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
    assert [e for e in page.errors if 'tiles.openfreemap' not in e] == []


def test_undo_restores(page):
    page.click('#undo2')
    assert page.is_hidden('#result-card')

# 상위 3개 약국은 "주변만 재계산"한 결과가 전체 재계산과 같은지 확인하는 테스트.
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import pytest
from analyze_bg import DATA, prepare, status_at


@pytest.fixture(scope='module')
def setup():
    bg, ph, _, _ = prepare()
    base = {i: status_at(b.geometry, ph, b.radius_m)[1] for i, b in bg.iterrows()}
    return bg, ph, base


@pytest.mark.parametrize('rank', [1, 2, 3])
def test_shortcut_matches_full_rerun(setup, rank):
    bg, ph, base = setup
    store = json.loads((DATA / 'cant_lose.json').read_text())['stores'][rank - 1]
    hit = ph.index[(ph.lat == store['lat']) & (ph.lon == store['lon'])]
    assert len(hit) == 1
    rest = ph.drop(index=hit)
    lost = {bg.at[i, 'GEOID'] for i, b in bg.iterrows()
            if base[i] != 'desert' and status_at(b.geometry, rest, b.radius_m)[1] == 'desert'}
    assert lost == set(store['block_groups'])

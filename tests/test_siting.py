# 후보지 점수와 PuLP 최적 조합이 말이 되는지 확인하는 테스트.
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import geopandas as gpd
import pytest
from analyze_bg import DATA, prepare
from siting import best_set, score


@pytest.fixture(scope='module')
def top_store():
    bg, ph, _, _ = prepare()
    s = json.loads((DATA / 'cant_lose.json').read_text())['stores'][0]
    rest = ph[~((ph.lat == s['lat']) & (ph.lon == s['lon']))]
    return bg[bg.GEOID.isin(s['block_groups'])], rest


def test_site_at_a_lost_block_restores_it(top_store):
    lost, rest = top_store
    b = lost.iloc[0]
    p = b.geometry.representative_point()
    cand = gpd.GeoDataFrame([{'name': 'test', 'kind': 'storefront', 'address': None, 'lat': 0, 'lon': 0}],
                            geometry=[p], crs=26986)
    restored = {r['GEOID'] for s in score(lost, rest, cand) for r in s['restored']}
    assert b['GEOID'] in restored


def test_saved_sites_are_consistent():
    out = json.loads((DATA / 'sites_out.json').read_text())
    for rank, s in out.items():
        for c in s['top']:
            assert c['gain'] == sum(r['pop'] for r in c['restored']) <= s['lost_pop']
            assert all(r['share_before'] < 15 <= r['share_after'] for r in c['restored'])
        if s['top']:
            assert s['top'][0]['gain'] <= s['best_set']['gain'] <= s['lost_pop']


def test_best_set_picks_complementary_sites():
    scored = [{'name': 'A', 'restored': [{'GEOID': 'x'}]}, {'name': 'B', 'restored': [{'GEOID': 'x'}]},
              {'name': 'C', 'restored': [{'GEOID': 'y'}]}]
    r = best_set(scored, {'x': 10, 'y': 5})
    assert r['gain'] == 15 and 'C' in r['sites']

# 순위와 블록그룹 상태 숫자가 서로 맞는지 확인하는 테스트.
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data'


def load():
    bg = json.loads((DATA / 'bg_out.geojson').read_text())['features']
    rank = json.loads((DATA / 'cant_lose.json').read_text())
    return [f['properties'] for f in bg], rank


def test_ranking_sums_to_near_desert_population():
    bg, rank = load()
    near = sum(p['pop'] for p in bg if p['s_state'] == 'near-desert')
    assert sum(s['people'] for s in rank['stores']) == near


def test_each_near_desert_block_group_belongs_to_exactly_one_store():
    bg, rank = load()
    near = {p['GEOID'] for p in bg if p['s_state'] == 'near-desert'}
    claimed = [g for s in rank['stores'] for g in s['block_groups']]
    assert len(claimed) == len(set(claimed))
    assert set(claimed) == near


def test_status_counts_cover_every_block_group():
    bg, _ = load()
    assert len(bg) == 462
    assert {p['s_state'] for p in bg} <= {'desert', 'near-desert', 'covered'}

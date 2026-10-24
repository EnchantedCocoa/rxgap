# 순위와 블록그룹 상태 숫자가 서로 맞는지 확인하는 테스트.
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data'


def load():
    bg = json.loads((DATA / 'bg_out.geojson').read_text())['features']
    rank = json.loads((DATA / 'cant_lose.json').read_text())
    return [f['properties'] for f in bg], rank


def test_ranking_covers_near_desert_population():
    # A block group can depend on more than one store (each covers a different slice),
    # so count each block group once.
    bg, rank = load()
    pop = {p['GEOID']: p['pop'] for p in bg}
    near = {p['GEOID'] for p in bg if p['s_state'] == 'near-desert'}
    claimed = {g for s in rank['stores'] for g in s['block_groups']}
    assert claimed == near
    assert sum(pop[g] for g in claimed) == sum(pop[g] for g in near)


def test_store_people_match_its_block_groups():
    bg, rank = load()
    pop = {p['GEOID']: p['pop'] for p in bg}
    for s in rank['stores']:
        assert s['people'] == sum(pop[g] for g in s['block_groups'])


def test_status_counts_cover_every_block_group():
    bg, _ = load()
    raw = json.loads((DATA / 'raw' / 'boston_bg.geojson').read_text())['features']
    assert len(bg) == len(raw) == 580
    assert {p['s_state'] for p in bg} <= {'desert', 'near-desert', 'covered'}

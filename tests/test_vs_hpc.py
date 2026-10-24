# 우리 블록그룹 판정이 주 정부(HPC) 공개 데이터와 얼마나 같은지 확인하는 테스트 (맞추려고 조정하지 않는다).
import json
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / 'data'
MAP = {'Pharmacy deserts': 'desert', 'Near deserts': 'near-desert', 'Non-deserts': 'covered'}


def test_agrees_with_state_on_most_residents():
    # HPC used June 2025 license data; we include closures and openings since. Some gap is expected.
    hpc = pd.read_csv(DATA / 'raw' / 'hpc' / 'hpc_bg_with_town.csv', dtype={'GEOID': str})
    ours = pd.DataFrame([f['properties'] for f in json.loads((DATA / 'bg_out.geojson').read_text())['features']])
    m = ours.merge(hpc[['GEOID', 'Category (HPC)']], on='GEOID')
    assert len(m) == len(ours) == 580
    same = m['pop'][m.s_state == m['Category (HPC)'].map(MAP)].sum() / m['pop'].sum()
    assert same >= 0.80

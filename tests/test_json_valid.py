# 앱이 읽는 JSON 파일에 NaN 같은 비표준 값이 없는지 확인하는 테스트 (브라우저는 NaN을 못 읽는다).
import json
from pathlib import Path
import pytest

DATA = Path(__file__).resolve().parent.parent / 'data'


def strict(s):
    def bad(c):
        raise ValueError(f'non-standard JSON value: {c}')
    return json.loads(s, parse_constant=bad)


@pytest.mark.parametrize('name', ['app_data.json', 'bg_out.geojson', 'cant_lose.json', 'sites_out.json', 'provenance.json'])
def test_strict_json(name):
    strict((DATA / name).read_text())

# 가짜 정사각형 블록그룹으로 사막·준사막·충족 판정 규칙을 확인하는 단위 테스트.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import geopandas as gpd
from shapely.geometry import Point, box
from analyze_bg import status_at

R = 500  # walk limit for these tests, meters
BG = box(0, 0, 1000, 1000)  # 1 km square block group


def stores(*xy):
    return gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in xy], crs=26986)


def test_no_store_is_desert():
    assert status_at(BG, stores(), R) == (0.0, 'desert')


def test_store_too_far_is_desert():
    assert status_at(BG, stores((5000, 5000)), R)[1] == 'desert'


def test_store_covering_under_15_percent_is_desert():
    # Corner store: quarter circle of r=300 covers ~7% of the square.
    share, s = status_at(BG, stores((0, 0)), 300)
    assert share < 0.15 and s == 'desert'


def test_single_store_is_near_desert():
    share, s = status_at(BG, stores((500, 500)), R)
    assert share > 0.15 and s == 'near-desert'


def test_two_stores_each_enough_is_covered():
    assert status_at(BG, stores((500, 500), (510, 500)), R)[1] == 'covered'

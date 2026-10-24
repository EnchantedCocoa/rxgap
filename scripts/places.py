# 분석할 장소(보스턴·스프링필드·플리머스)의 설정과 입출력 경로를 한곳에 모은 모듈.
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
MANUAL = ROOT / 'data' / 'manual'

PLACES = {
    'boston': {'name': 'Boston', 'county': '025', 'council': True,
               'npi_zips': [f'021{n:02d}' for n in range(8, 38)] + ['02163', '02199', '02210', '02215', '02138', '02139',
                            '02140', '02141', '02142', '02143', '02144', '02145', '02148', '02149', '02150', '02151',
                            '02152', '02169', '02170', '02171', '02186', '02026', '02445', '02446', '02447', '02458',
                            '02459', '02467', '02472', '02368', '02021', '02090', '02494'],
               'view': [42.295, -71.085, 13]},
    'springfield': {'name': 'Springfield', 'county': '013', 'council': False,
                    'npi_zips': [f'011{n:02d}' for n in range(1, 52)] + ['01001', '01013', '01020', '01022', '01028',
                                 '01030', '01036', '01040', '01056', '01057', '01077', '01089', '01095', '01106', '01118'],
                    'view': [42.11, -72.56, 13],
                    'why': 'Most residents at risk of any large Massachusetts city'},
    'plymouth': {'name': 'Plymouth', 'county': '023', 'council': False,
                 'npi_zips': ['02360', '02361', '02362', '02364', '02366', '02367', '02330', '02571', '02538', '02532',
                              '02559', '02561', '02562', '02563', '02332', '02338', '02347', '02345'],
                 'view': [41.89, -70.62, 11],
                 'why': 'Most residents at risk of any mostly-suburban town'},
}

SLUG = os.environ.get('RXGAP_PLACE', 'boston')
PLACE = PLACES[SLUG]
# Boston keeps its original paths; other places live in their own folders.
OUT = ROOT / 'data' if SLUG == 'boston' else ROOT / 'data' / 'places' / SLUG
BG_FILE = RAW / 'boston_bg.geojson' if SLUG == 'boston' else RAW / 'places' / f'{SLUG}_bg.geojson'
ACS_FILE = RAW / 'acs_bg.json' if SLUG == 'boston' else RAW / 'places' / f'{SLUG}_acs.json'
SITES_FILE = RAW / 'sites.json' if SLUG == 'boston' else RAW / 'places' / f'{SLUG}_sites.json'
WALK_FILE = RAW / 'walk.gpickle' if SLUG == 'boston' else RAW / 'places' / f'{SLUG}_walk.gpickle'
OUT.mkdir(parents=True, exist_ok=True)
(RAW / 'places').mkdir(exist_ok=True)

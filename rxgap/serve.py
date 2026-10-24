# 앱과 데이터 폴더만 127.0.0.1에서 제공하고, 선거구별 편지 수(이름·주소 없이)를 DuckDB에 세는 로컬 서버.
import csv, http.server, json, os, sys, threading
from datetime import date
from functools import partial
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = ('/app/', '/data/')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
DB_PATH = Path(os.environ.get('RXGAP_DB', ROOT / 'data' / 'letters.duckdb'))  # tests point this elsewhere
MAX_BODY = 1024


def known_districts():
    with open(ROOT / 'data' / 'manual' / 'officials.csv') as f:
        return {(r['district_type'], r['district_id']) for r in csv.DictReader(f)}


class Counts:
    """Letter counts by district and day. Stores no names, addresses or letter text."""

    def __init__(self, path):
        self.db = duckdb.connect(str(path))
        self.db.execute('CREATE TABLE IF NOT EXISTS letters (district_type TEXT, district_id TEXT, day DATE, n INTEGER,'
                        ' PRIMARY KEY (district_type, district_id, day))')
        self.lock = threading.Lock()
        self.ok = known_districts()

    def add(self, kind, did):
        if (kind, did) not in self.ok:
            return False
        with self.lock:
            self.db.execute('INSERT INTO letters VALUES (?, ?, ?, 1) ON CONFLICT DO UPDATE SET n = n + 1',
                            [kind, did, date.today()])
        return True

    def all(self):
        with self.lock:
            rows = self.db.execute('SELECT district_type, district_id, SUM(n) FROM letters GROUP BY 1, 2 ORDER BY 1, 2').fetchall()
        return [{'district_type': k, 'district_id': d, 'letters': int(n)} for k, d, n in rows]


class Handler(http.server.SimpleHTTPRequestHandler):
    counts = None

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/app/')
            self.end_headers()
            return
        if path == '/counts':
            return self._json(200, self.counts.all())
        if not path.startswith(ALLOWED) or '/.' in path or '..' in path:
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != '/count':
            return self._json(404, {'error': 'not found'})
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0 or n > MAX_BODY:
            return self._json(400, {'error': 'bad size'})
        try:
            b = json.loads(self.rfile.read(n))
            ok = self.counts.add(str(b['district_type']), str(b['district_id']))
        except (ValueError, KeyError, TypeError):
            ok = False
        return self._json(200 if ok else 400, {'ok': ok})

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def main():
    Handler.counts = Counts(DB_PATH)
    handler = partial(Handler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(('127.0.0.1', PORT), handler) as srv:
        print(f'RxGap on http://127.0.0.1:{PORT}/app/  (local only, no login)')
        srv.serve_forever()


if __name__ == '__main__':
    main()

# 앱과 데이터 폴더만 127.0.0.1에서 제공하는 로컬 서버 (.env 등 다른 파일은 막는다).
import http.server
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = ('/app/', '/data/')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/app/')
            self.end_headers()
            return
        if not path.startswith(ALLOWED) or '/.' in path or '..' in path:
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def main():
    handler = partial(Handler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(('127.0.0.1', PORT), handler) as srv:
        print(f'RxGap on http://127.0.0.1:{PORT}/app/  (local only, no login)')
        srv.serve_forever()


if __name__ == '__main__':
    main()

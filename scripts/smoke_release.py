"""Exercise production WSGI and static assets over loopback; always stop the server.

Run migrations and collectstatic first. This does not test a hosted TLS proxy.
"""
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


def main():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    env = dict(os.environ, DJANGO_DEBUG='False', DJANGO_SECRET_KEY=secrets.token_urlsafe(60),
               DJANGO_ALLOWED_HOSTS='127.0.0.1', SECURE_SSL_REDIRECT='False',
               HOST='127.0.0.1', PORT=str(port))
    base = f'http://127.0.0.1:{port}'
    process = subprocess.Popen([sys.executable, 'scripts/serve.py'], cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError('Waitress exited before startup; check deployment settings.')
            try:
                with urlopen(base + '/health/', timeout=2) as response:
                    assert response.status == 200
                break
            except URLError:
                time.sleep(.2)
        else:
            raise RuntimeError('Timed out waiting for Waitress.')
        for path in ['/', '/creators/', '/accounts/login/']:
            with urlopen(base + path, timeout=10) as response:
                html = response.read().decode()
                assert response.status == 200
                assert response.headers.get('X-Content-Type-Options') == 'nosniff'
            print('PASS HTTP', path)
            if path == '/':
                assets = set(re.findall(r'(?:src|href)="(/static/[^"]+)"', html))
                assert len(assets) >= 4, 'Expected local CSS and JS assets'
                for asset in assets:
                    with urlopen(base + asset, timeout=10) as response:
                        assert response.status == 200 and response.read(), asset
                print('PASS static assets:', len(assets))
        for path in ['/media/evidence/private.png', '/media/portfolios/missing.png']:
            try:
                urlopen(base + path, timeout=5)
            except HTTPError as exc:
                assert exc.code == 404, (path, exc.code)
            else:
                raise AssertionError('Unexpected file exposure: ' + path)
        print('PASS media access boundaries')
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == '__main__':
    main()

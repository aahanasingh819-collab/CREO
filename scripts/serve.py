"""Production WSGI entry point; put an HTTPS reverse proxy in front."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.wsgi import application
from waitress import serve

if __name__ == '__main__':
    proxy = os.getenv('TRUSTED_PROXY_IP')
    serve(application, host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('PORT', '3000')),
          threads=4, max_request_body_size=6 * 1024 * 1024,
          trusted_proxy=proxy, trusted_proxy_headers={'x-forwarded-proto'} if proxy else set())

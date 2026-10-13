"""Render free web service: migrations at startup (no paid pre-deploy job)."""
import os
import subprocess
import sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
if os.getenv('SEED_DEMO', 'False').lower() == 'true':
    subprocess.run([sys.executable, 'manage.py', 'seed_demo'], check=True)
os.execv(sys.executable, [sys.executable, 'scripts/serve.py'])

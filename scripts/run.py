"""Simple entrypoint to run the app in development with one command.

Usage:
    py -3 run.py
    py -3 run.py --port 9000
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    try:
        result = subprocess.run(cmd)
    except KeyboardInterrupt:
        raise SystemExit(130)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run Django app with defaults')
    parser.add_argument('--host', default='127.0.0.1', help='Host bind (default: 127.0.0.1)')
    parser.add_argument('--port', default='8000', help='Port bind (default: 8000)')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    manage_py = project_root / 'manage.py'

    run_command([sys.executable, str(manage_py), 'migrate'])
    run_command([sys.executable, str(manage_py), 'runserver', f'{args.host}:{args.port}'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)

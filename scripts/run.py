"""Simple entrypoint to run the app in development with one command.

Usage:
    py -3 run.py
    py -3 run.py --port 9000
"""

from __future__ import annotations

import argparse
import calendar
from datetime import date
import os
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


def bootstrap_django(project_root: Path) -> None:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecci_carbon_footprint_dj.settings')

    import django

    django.setup()


def should_load_seed_data(project_root: Path) -> bool:
    bootstrap_django(project_root)

    from carbon_footprint.models import Campus, FuelType, Period

    return not (Campus.objects.exists() and FuelType.objects.exists() and Period.objects.exists())


def ensure_default_periods(project_root: Path) -> None:
    bootstrap_django(project_root)

    from carbon_footprint.models import Period

    if Period.objects.exists():
        return

    start_year = 2022
    end_year = max(date.today().year, start_year)

    for year in range(start_year, end_year + 1):
        Period.objects.get_or_create(
            year=year,
            month=None,
            defaults={
                'start_date': date(year, 1, 1),
                'end_date': date(year, 12, 31),
            },
        )

        for month in range(1, 13):
            _, last_day = calendar.monthrange(year, month)
            Period.objects.get_or_create(
                year=year,
                month=month,
                defaults={
                    'start_date': date(year, month, 1),
                    'end_date': date(year, month, last_day),
                },
            )


def main() -> None:
    parser = argparse.ArgumentParser(description='Run Django app with defaults')
    parser.add_argument('--host', default='127.0.0.1', help='Host bind (default: 127.0.0.1)')
    parser.add_argument('--port', default='8000', help='Port bind (default: 8000)')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    manage_py = project_root / 'manage.py'
    fixture_path = project_root / 'carbon_footprint' / 'fixtures' / 'initial_data.json'

    run_command([sys.executable, str(manage_py), 'migrate'])

    if fixture_path.exists() and should_load_seed_data(project_root):
        run_command([sys.executable, str(manage_py), 'loaddata', str(fixture_path)])

    ensure_default_periods(project_root)

    run_command([sys.executable, str(manage_py), 'runserver', f'{args.host}:{args.port}'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)

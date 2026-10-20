#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate --noinput
# Existing sample database is preserved. For an empty disposable local DB only,
# run: DJANGO_DEBUG=1 .venv/bin/python manage.py seed_demo
exec .venv/bin/python manage.py runserver 127.0.0.1:8000

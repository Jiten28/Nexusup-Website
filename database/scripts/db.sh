#!/usr/bin/env bash
# NexusUp database helper for macOS and Linux.   Usage: ./db.sh <command> [argument]
# Needs Docker Desktop (running). Reads database/.env. Never touches your SQLite file except to read it.
set -euo pipefail
DB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$DB_DIR/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$DB_DIR"
[ -f .env ] || { echo "Missing database/.env - run:  cp database/.env.example database/.env  and set the passwords."; exit 1; }
set -a; . ./.env; set +a
DC=(docker compose --env-file .env -f compose.yaml)
PY="$BACKEND/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
mariadb_env() {   # environment the Django backend needs to talk to this MariaDB
  export DB_ENGINE=mariadb DB_NAME DB_USER DB_PASSWORD DB_HOST=127.0.0.1 DB_PORT="${DB_PORT:-3306}" DJANGO_DEBUG=1
}
wait_ready() { echo -n "Waiting for MariaDB"; for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' nexusup-db 2>/dev/null || true)" = healthy ] && { echo " ready."; return; }; echo -n .; sleep 2; done
  echo; echo "MariaDB did not become healthy. Check: docker compose logs db"; exit 1; }
cmd="${1:-help}"; arg="${2:-}"
case "$cmd" in
  up)      "${DC[@]}" up -d db; wait_ready ;;
  down)    "${DC[@]}" stop db; echo "Stopped. Your data is kept in the Docker volume." ;;
  status)  "${DC[@]}" ps; ( mariadb_env; cd "$BACKEND" && "$PY" manage.py shell -c "from django.db import connection as c; c.ensure_connection(); print('Django connected to', c.vendor, c.settings_dict['NAME'], 'on', c.settings_dict['HOST'])" ) ;;
  create)  # create the tables (runs Django migrations against MariaDB)
           "${DC[@]}" up -d db; wait_ready; ( mariadb_env; cd "$BACKEND" && "$PY" manage.py migrate ) ;;
  export)  # whole database -> database/backups/nexusup-<time>.sql
           out="${arg:-$DB_DIR/backups/nexusup-$(date +%Y%m%d-%H%M%S).sql}"; mkdir -p "$(dirname "$out")"
           "${DC[@]}" exec -T db sh /scripts/export.sh
           docker cp nexusup-db:/tmp/export.sql "$out"; echo "Exported to $out" ;;
  import)  # load a .sql file made by "export" (replaces matching tables)
           [ -f "$arg" ] || { echo "Usage: ./db.sh import path/to/file.sql"; exit 1; }
           echo "This will overwrite tables in database '$DB_NAME'. Press Enter to continue, Ctrl+C to cancel."; read -r _
           "${DC[@]}" up -d db; wait_ready; docker cp "$arg" nexusup-db:/tmp/import.sql
           "${DC[@]}" exec -T db sh /scripts/import.sh; echo "Imported $arg" ;;
  from-sqlite) # copy articles/sources/categories from your SQLite file into an EMPTY MariaDB
           sqlite="${arg:-$BACKEND/demo.sqlite3}"; [ -f "$sqlite" ] || { echo "SQLite file not found: $sqlite"; exit 1; }
           dump="$DB_DIR/backups/sqlite-data-$(date +%Y%m%d-%H%M%S).json"; mkdir -p "$DB_DIR/backups"
           echo "Reading (read-only) $sqlite"
           ( cd "$BACKEND"; DB_ENGINE=sqlite DJANGO_DEBUG=1 SQLITE_PATH="$sqlite" "$PY" manage.py dumpdata --natural-foreign --natural-primary \
               --exclude contenttypes --exclude auth.permission --exclude sessions --exclude admin.logentry --indent 1 --output "$dump" )
           "${DC[@]}" up -d db; wait_ready
           ( mariadb_env; cd "$BACKEND"; "$PY" manage.py migrate
             if ! "$PY" manage.py shell -c "import sys; from apps.news.models import Article; sys.exit(1 if Article.objects.exists() else 0)"; then
               echo "MariaDB already contains articles - refusing to import on top of them. Use './db.sh export' first, or a fresh volume."; exit 1; fi
             "$PY" manage.py loaddata "$dump" ); echo "Done. Intermediate file kept at $dump (delete it when you are happy)." ;;
  reset)   echo "This DELETES the MariaDB volume and all its data. Type RESET to continue:"; read -r a; [ "$a" = RESET ] && { "${DC[@]}" down -v; echo "Volume removed."; } ;;
  *)       cat <<USAGE
Commands:
  up                start MariaDB in Docker
  create            create all tables (Django migrate)
  status            show container state and test the Django connection
  export [file]     save the whole database to database/backups/*.sql
  import <file>     restore a .sql file
  from-sqlite [db]  copy your existing SQLite data into an empty MariaDB (SQLite is only read)
  down              stop MariaDB (data is kept)
  reset             delete the MariaDB volume (asks for confirmation)
USAGE
           ;;
esac

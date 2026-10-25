#!/bin/sh
# Runs INSIDE the MariaDB container. Writes /tmp/export.sql (full database, UTF-8).
exec mariadb-dump -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" --single-transaction --routines \
  --default-character-set=utf8mb4 --result-file=/tmp/export.sql "$MARIADB_DATABASE"

#!/bin/sh
# Runs INSIDE the MariaDB container. Loads /tmp/import.sql into the NexusUp database.
exec mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" --default-character-set=utf8mb4 "$MARIADB_DATABASE" -e 'source /tmp/import.sql'

# Backup, restore and persistence verification

Use the host's managed encrypted snapshot facility when available; otherwise use MariaDB tools matching the service version. Back up the **database and media together** before an upgrade. Store encrypted/off-host copies with tested retention and restricted access. Record release ID, migration revision, time, checksums and restoration procedure. Do not commit backups, credential files or private data to the project repository.

## MariaDB logical backup

Configure an owner-readable client option file outside the repo (mode 0600) with `[client]` credentials/host/TLS settings. Never put the password on the command line.

```sh
mariadb-dump --defaults-extra-file=/secure/db-client.cnf --single-transaction \
  --routines --events --triggers --hex-blob --default-character-set=utf8mb4 \
  nexusup > /secure/backups/nexusup.sql
# Pause writes while pairing DB and media snapshot, or use coordinated storage snapshots.
tar -C /srv/nexusup-persistent -czf /secure/backups/media.tar.gz media
sha256sum /secure/backups/nexusup.sql /secure/backups/media.tar.gz
```

No reset, drop or recreate is part of backup. `--single-transaction` assumes transactional tables and no concurrent schema changes. For object media use versioned bucket replication/snapshots or a verified object inventory and copy. Volume snapshots alone must be consistent with DB transaction state.

## Isolated restore drill

1. Create a separate restricted restore database and media location. Never restore over production without explicit authorization and a downtime/rollback plan.
2. Verify backup checksums and target database identity. Restore using a private option file pointing to the isolated target: `mariadb --defaults-extra-file=/secure/restore-client.cnf nexusup_restore < /secure/backups/nexusup.sql`.
3. Inspect archive paths before extracting media; restore into the isolated persistent directory with correct service ownership. Object storage keys must be preserved.
4. Point an isolated app release at restored DB/media; compare model counts, migration state, FK consistency, drafts/published visibility, sources and trust flags, article images, admin and Unicode content. Do not run migrations blindly ahead of the backed-up release.
5. Restart and recreate app processes (not DB/media volumes) and repeat checks. Confirm scheduler is disabled in the restore environment to prevent unintended fetching/publication.
6. Record observed recovery time and accepted recovery point. Only after a successful drill approve production backup policy.

## SQLite development preservation

Use SQLite's backup API rather than copying a live write-in-progress file. Stop local writers or take an API backup. `PRAGMA integrity_check` and `PRAGMA foreign_key_check` must pass. Retain the original supplied archive in `docs/archive/recovery/` as the recoverable historical input. Do not use the demo reset/seed command for a client database.

## Compose

Back up named `database` and `media` volumes via consistent DB dump plus media snapshot, or the host's approved coordinated snapshot tooling. Plain volume file copies while MariaDB is running are not an accepted logical backup. Avoid exposing root passwords in `docker exec` arguments. **Never run `docker compose down -v` in production.** A release rollback is not a license to erase persistent volumes.

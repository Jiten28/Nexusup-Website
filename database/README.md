# Database and migration ownership

This folder contains documentation, not the running database. Production is a persistent MariaDB service. The existing `backend/demo.sqlite3` remains a development database. It contains ten original illustrative articles, twelve categories and two disabled source candidates. Never point production at it or auto-seed during deployment.

Django 5.2 uses `django.db.backends.mysql` with mysqlclient 2.2.7+; MariaDB 10.5+ is supported, and optional Compose targets MariaDB 11.4 LTS. Required host client/development libraries are documented in `docs/DEPLOYMENT.md`. No actual MariaDB server or credentials were available during implementation. MariaDB execution is a required host acceptance step.

Keep migrations inside `backend/apps/news/migrations`. Historical app label `news`, table names and existing 0001/0002 migration bytes are preserved. 0003 adds explicit source trust, tags and title hash; 0004 adds publisher attribution and a unique nullable title hash. Existing empty hash defaults are converted to NULL before uniqueness; duplicate existing hash markers are cleared for later records, **not** article deletion. Original article content is not rewritten. New sources remain untrusted by default.

## New empty MariaDB service (operator only)

Create a database with utf8mb4 and a case-sensitive/binary collation where appropriate (e.g. `utf8mb4_bin`). Create an application user restricted to that database and a private host; a separate migration role may be used under the host's policy. Supply credentials privately; no root user in Django. Restrict network exposure and use TLS + CA for remote service. Do not use example passwords as real credentials.

Run `manage.py migrate --plan`, backup if not empty, then `manage.py migrate`. The command does not import the supplied samples. Use `manage.py createsuperuser` interactively on the approved host; no admin credentials are shipped in frontend configuration.

## Optional SQLite-to-MariaDB sample/content transfer

This is opt-in, not required by React. Review whether samples belong in the destination. Back up both stores and test on an isolated empty MariaDB first. Export with the source settings and import with the destination settings at the same migration revision:

```sh
# Source SQLite, debug enabled only in controlled local environment:
DJANGO_DEBUG=1 DB_ENGINE=sqlite python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude sessions > /secure/nexusup-transfer.json
# Switch to private production MariaDB settings, migrate and inspect destination first.
python manage.py migrate --plan
python manage.py migrate
python manage.py loaddata /secure/nexusup-transfer.json
```

Do not run `loaddata` into an existing client database without a reconciliation plan: primary keys can conflict or overwrite records. The transfer includes sensitive user hashes and private messages if present; secure it and remove it after verified transfer. Move media separately preserving keys. Compare per-model counts, public/draft status, foreign keys, auth/admin access, Unicode search, slug/canonical/title uniqueness and sample labels. Test ingestion transactions, duplicate races and migration application on the actual MariaDB collation. Keep the SQLite backup untouched for recovery. This transfer was not executed against MariaDB.

Troubleshooting: verify DNS/private networking/port, driver import and client library, database grants/name/user, CA path/hostname, utf8mb4 support, server version and migration history. Never fix a failed connection by enabling DEBUG in production, allowing every host, dropping tables or resetting migrations.

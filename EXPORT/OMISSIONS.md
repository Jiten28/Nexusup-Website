# Export omissions and representation changes

Application source, templates, migrations, tests, lockfiles, configuration templates, media and documentation are included unless explicitly listed below.
No feature fix/removal was applied during packaging. Exclusions affect dependencies, generated/historical artifacts, private configuration or repository metadata.
Root and backend private .env files were absent at packaging. They would be excluded if present. Safe example templates are included unchanged.

## Excluded paths

- `.git/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/apps/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/apps/news/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/apps/news/management/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/apps/news/management/commands/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/apps/news/migrations/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/config/__pycache__/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `backend/staticfiles/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `docs/archive/recovery/NexusUp_Django_Demo.zip` — Nested historical recovery/archive bundle excluded; may contain obsolete configuration or credentials. Current source is included directly.
- `docs/verification/**` — Generated historical verification artifacts/logs/screenshots; source tests and narrative documentation are retained. Historical results are not current acceptance evidence.
- `frontend/dist-demo/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `frontend/dist/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.
- `frontend/node_modules/**` — Git metadata, installed dependency, cache, generated build or test output; reinstall/rebuild when needed.

## Database snapshot

backend/demo.sqlite3 IS INCLUDED. It was rebuilt with SQLite VACUUM INTO in export staging from a read-only source connection. This removes deleted/free-page remnants, not logical records.
All logical table records match the source snapshot. The source database was not changed. Integrity and foreign-key checks pass on the export.
No usable password hashes, active/private user accounts, sessions, contacts, comments, admin logs or non-sample articles were present.
Included data: 10 published sample articles, two disabled BBC source candidates, zero imported articles and zero fetch runs. This is NOT the unidentified Windows database.

## Existing deletions

The current working tree already lacks backend/scripts/browser_qa.cjs and backend/scripts/enhancement_qa.cjs. They are not restored silently; historical versions exist under docs/archive/legacy-tests/.

## Rebuild/install

Recreate Python/node dependencies using requirements.txt and package-lock.json. Build the frontend with npm run build when desired. See WINDOWS_SETUP.md.
Git metadata/history is omitted; the exact base commit and file hashes are in VERSION.json/MANIFEST.json. This is a source snapshot, not a Git checkout.

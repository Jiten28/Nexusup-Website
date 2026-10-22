# NexusUp — portable React + Django news portal

An incremental migration of the supplied Django application, not a new content dataset.

- **Public frontend:** React + Vite, one horizontal image carousel, centered editorial feature, responsive grid, controlled Load More, six coordinated palettes with independent light/dark, retained utilities.
- **Backend:** Django 5.2 + DRF; existing app label, tables, manual editorial workflow, forms, admin, routes, SQLite development records and seven media files preserved.
- **Production:** MariaDB + Gunicorn + persistent media + independent scheduler. Static frontend can live on any compatible host. Netlify is optional.
- **Ingestion:** rights-gated RSS/Atom and optional NewsAPI metadata adapter; separate trust/auto-publication flags, review-by-default, canonical/title/provider-ID deduplication and fetch logs.

## Client demo preview

For the polished, explicitly labeled frontend preview, follow `docs/FRONTEND_DEMO.md`. Run `npm run demo -- --port 5174` with the existing local backend. Normal `npm run dev` and `npm run build` remain API-only; the separate opt-in build is `npm run build:demo` (`dist-demo/`).

## Local development (two terminals)

Python 3.12/3.13 and Node 22+ recommended. These commands do not reseed the supplied database.

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
# Review backend/.env.example; examples are NOT loaded automatically.
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

```sh
cd frontend
npm i
npm run dev
```

Open the Vite URL printed in the terminal. Its development proxy serves `/api` and `/media` from Django. Do not use Django's fallback homepage as the React preview. It remains available for legacy compatibility.

## Handover documents

- `docs/AUDIT.md` — original Stage 1 findings; deliberately historical.
- `docs/HANDOVER.md` — completed work, feature checklist, actual verification and remaining blockers.
- `docs/DEPLOYMENT.md` — provider-neutral Python/VPS and optional Compose deployments, origins, static/media, scheduler, rollback and Netlify diagnosis.
- `database/README.md` and `database/backup-restore.md` — MariaDB setup and preservation/restore procedure.
- `docs/FILE_CHANGES.md` and `docs/file-manifest.json` — before/after trees and exact file actions.
- `docs/verification/` — executed test evidence. Historical reports in `docs/archive/` are **not** current acceptance results.

No production deployment, DNS change, paid account activation or live MariaDB connection has been performed. Provider integrations ship disabled; sample stories remain labeled. Do not publish the bundled reference media without confirming rights. The preview is intentionally noindex; legal/editorial approval and a production robots policy are launch gates.

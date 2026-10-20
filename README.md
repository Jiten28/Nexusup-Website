# NexusUp — Portable React + Django News Portal

An incremental migration of the supplied Django application, not a new content dataset.

## 1. Project Overview

### Public frontend

- React + Vite.
- One horizontal image carousel.
- Centered editorial feature and responsive news grid.
- Controlled **Load More** functionality.
- Four independent color palettes with light/dark modes.
- Existing utilities retained.

### Backend

- Django 5.2 + Django REST Framework (DRF).
- Existing Django app label, database tables, editorial workflow, forms, admin, and routes preserved.
- SQLite development records and all seven supplied media files retained.
- No automatic database reseeding.

### Production

- MariaDB + Gunicorn + persistent media storage.
- Independent scheduler for background ingestion.
- Frontend deployable to any compatible static hosting provider.
- Netlify is optional, not required.

### News ingestion

- Rights-gated RSS/Atom ingestion.
- Optional NewsAPI metadata adapter.
- Separate source-trust and auto-publication flags.
- Review-by-default workflow.
- Canonical URL, title, and provider-ID deduplication.
- Fetch logs for monitoring ingestion attempts.

## 2. Prerequisites

Recommended versions:

- Python 3.12 or 3.13.
- Node.js 22 or later.
- npm, included with Node.js.
- Git, if you are cloning the project repository.

Install Python and Node.js using their official websites:

- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/en/download/
- Git: https://git-scm.com/downloads

After installation, open a new terminal and verify the installations.

**Windows — PowerShell**

```powershell
py --version
node --version
npm --version
git --version
```

**macOS — Terminal**

```bash
python3 --version
node --version
npm --version
git --version
```

If Git is not needed because the project folder is already available, you can skip checking Git.

## 3. Local Development — Windows

Use two separate PowerShell terminals: one for Django and one for React.

### Terminal 1 — Django backend

Open PowerShell in the NexusUp project folder and run:

```powershell
cd backend

py -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
```

Review `backend/.env` and configure the settings appropriate for your local environment. The `.env.example` file is a template and is not loaded automatically.

If you do not want to create a local `.env` file yet, skip the `Copy-Item` command and configure the environment variables explicitly instead.

Enable Django development mode in the current PowerShell session:

```powershell
$env:DJANGO_DEBUG = "1"
```

Apply database migrations and start Django:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

The backend should now be available at:

`http://127.0.0.1:8000/`

**If PowerShell blocks virtual-environment activation**, run this in the same terminal and try activation again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This changes the execution policy for the current PowerShell process only.

### Terminal 2 — React frontend

Open a second PowerShell terminal in the project folder:

```powershell
cd frontend

npm ci
npm run dev
```

Open the Vite URL printed in the terminal, commonly:

`http://localhost:5173/`

The Vite development proxy should forward `/api` and `/media` requests to Django.

Keep both terminals running while developing.

## 4. Local Development — macOS

Use two separate Terminal windows or tabs: one for Django and one for React.

### Terminal 1 — Django backend

From the NexusUp project folder, run:

```bash
cd backend

python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
```

Review `backend/.env` and configure the appropriate local settings. The `.env.example` file is a template and is not loaded automatically.

If you prefer to configure environment variables directly, skip the `cp` command.

Enable Django development mode in the current terminal:

```bash
export DJANGO_DEBUG=1
```

Apply migrations and start Django:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

The backend should now be available at:

`http://127.0.0.1:8000/`

### Terminal 2 — React frontend

Open a second Terminal window or tab in the project folder:

```bash
cd frontend

npm ci
npm run dev
```

Open the Vite URL printed in the terminal, commonly:

`http://localhost:5173/`

The Vite development proxy should forward `/api` and `/media` requests to Django.

Keep both terminals running while developing.

## 5. Database and Media Preservation

The supplied SQLite database and media files must remain intact throughout local development.

- Do not run seed scripts, fixture imports, or database reset commands unless explicitly intended.
- `python manage.py migrate` applies pending migrations; it does not automatically reseed the database.
- Back up the SQLite database and media directory before schema changes.
- Verify the configured SQLite database path before running migrations.
- Preserve the existing Django app label, table names, editorial records, forms, admin, and routes.
- Confirm the presence of all seven supplied media files.
- Do not publish reference media until usage rights are confirmed.

For production, follow the database backup and restore procedures before migrating from SQLite to MariaDB.

## 6. Handover Documents

- `docs/AUDIT.md` — original Stage 1 findings; historical reference.
- `docs/HANDOVER.md` — completed work, feature checklist, verification results, and remaining blockers.
- `docs/DEPLOYMENT.md` — provider-neutral Python/VPS and optional Compose deployments, allowed origins, static/media handling, scheduler, rollback, and Netlify troubleshooting.
- `database/README.md` — MariaDB setup.
- `database/backup-restore.md` — database preservation and restoration procedure.
- `docs/FILE_CHANGES.md` — file-level changes.
- `docs/file-manifest.json` — before/after file trees and exact file actions.
- `docs/verification/` — executed test evidence.
- `docs/archive/` — historical reports that are not current acceptance results.

## 7. Production Readiness and Launch Gates

The following must not be treated as completed without verification:

- Production deployment, DNS changes, paid account activation, and a live MariaDB connection.
- Production environment variables, secrets, and allowed-origin configuration.
- Persistent media storage and a tested backup/restore process.
- Independent scheduler deployment and monitoring.
- Provider integrations, which ship disabled.
- Sample stories, which remain labeled.
- Editorial and legal approval of content and media rights.
- Production `robots.txt`, indexing policy, and removal of preview-only `noindex` directives when appropriate.

The preview is intentionally configured as noindex. Confirm the final production indexing policy before launch.

## 8. Important Notes

- Use the React/Vite URL for the public frontend preview, not Django's fallback homepage.
- Django's fallback homepage remains available for legacy compatibility.
- Use the same Python version and compatible dependencies across development and deployment.
- Keep credentials out of source control. Ensure `.env` files are excluded from Git.
- Do not assume that a successful local run proves production readiness.
- Check `docs/HANDOVER.md` and `docs/verification/` for the actual state of completed work and outstanding issues.

**Local development is ready to begin once dependencies are installed and the existing database, environment configuration, and media paths have been verified.**

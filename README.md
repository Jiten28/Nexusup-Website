# NexusUp

A news website with a **React** front end, a **Django** back end and a **MariaDB** database.
It collects headlines from publishers you have approved (RSS feeds or NewsAPI), lets an editor review them, and shows them on a fast, themeable homepage.

```
NexusUp/
├── backend/    Django + REST API: admin, news fetching, translation, image rules
├── frontend/   React + Vite: the website visitors see
├── database/   MariaDB in Docker + scripts to create, export, import and migrate data
└── docs/       NEWS.md (fetching, images, translation) · TESTING.md · CHANGELOG.md
```

**How the parts talk:** browser → `frontend` (port 5173) → `/api` requests are forwarded to `backend` (port 8000) → `database`.
The backend never fetches news while a visitor waits; news is fetched only when you run a command.

---

## 1. What you need

| Tool | Version | Check with |
|---|---|---|
| Python | 3.12 or 3.13 | `python --version` (Windows) · `python3 --version` (Mac) |
| Node.js | 22 or newer | `node --version` |
| Docker Desktop | any recent | `docker --version` (only needed for MariaDB) |

Install Python from python.org (tick **Add python.exe to PATH** on Windows), Node from nodejs.org, Docker from docker.com.

## 2. Quick start (SQLite, no Docker)

Open **two** terminals in the `NexusUp` folder.

**Terminal 1: backend**

Windows (PowerShell)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env           # your private settings (never commit this file)
python manage.py migrate
python manage.py createsuperuser      # admin login for http://127.0.0.1:8000/admin/
python manage.py runserver 127.0.0.1:8000
```

Mac / Linux
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

**Terminal 2: frontend** (same on both systems)
```
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173**. The admin is at **http://127.0.0.1:8000/admin/**.

> Your existing `backend/demo.sqlite3` is used automatically. `migrate` only adds missing tables; it never deletes articles.

## 3. Using MariaDB (what the client wants)

MariaDB runs in Docker, so nothing is installed on your computer except Docker Desktop.
The helper script is `database/scripts/db.ps1` (Windows) or `database/scripts/db.sh` (Mac/Linux). Run it from the `NexusUp` folder.

**Step 1: passwords**

| Windows | Mac / Linux |
|---|---|
| `Copy-Item database\.env.example database\.env` | `cp database/.env.example database/.env` |

Open `database/.env` and set `DB_PASSWORD` and `DB_ROOT_PASSWORD` to your own values.

**Step 2: tell Django to use it.** In `backend/.env` set:
```
DB_ENGINE=mariadb
DB_NAME=nexusup
DB_USER=nexusup
DB_PASSWORD=<same as database/.env>
DB_HOST=127.0.0.1
DB_PORT=3306
```

**Step 3: start MariaDB and create the tables**

| | Windows | Mac / Linux |
|---|---|---|
| Start | `.\database\scripts\db.ps1 up` | `./database/scripts/db.sh up` |
| Create tables | `.\database\scripts\db.ps1 create` | `./database/scripts/db.sh create` |
| Check connection | `.\database\scripts\db.ps1 status` | `./database/scripts/db.sh status` |

Then run `createsuperuser` and `runserver` as in section 2. Django now reads and writes MariaDB.

### Copy your existing data from SQLite into MariaDB

```
Windows:    .\database\scripts\db.ps1 from-sqlite
Mac/Linux:  ./database/scripts/db.sh from-sqlite
```
It reads `backend/demo.sqlite3` (read-only, the file is never changed), saves a JSON copy in `database/backups/`, creates the tables in MariaDB and loads the data.
It refuses to run if MariaDB already contains articles, so it cannot overwrite anything. Use `from-sqlite path\to\other.sqlite3` for a different file.

### Export and import (backups)

| | Windows | Mac / Linux |
|---|---|---|
| Export everything to `database/backups/nexusup-<time>.sql` | `.\database\scripts\db.ps1 export` | `./database/scripts/db.sh export` |
| Restore a file (asks first) | `.\database\scripts\db.ps1 import database\backups\file.sql` | `./database/scripts/db.sh import database/backups/file.sql` |
| Stop (data is kept) | `.\database\scripts\db.ps1 down` | `./database/scripts/db.sh down` |
| Delete all data (asks first) | `.\database\scripts\db.ps1 reset` | `./database/scripts/db.sh reset` |

Data lives in the Docker volume `nexusup_mariadb`. For a client's hosted MariaDB, keep `DB_ENGINE=mariadb` and change `DB_HOST`, `DB_USER`, `DB_PASSWORD`; for production also set `DB_SSL_CA` (see `backend/.env.example`) and `DJANGO_DEBUG=0`.

## 4. Getting news

Nothing is fetched automatically. Run these from `backend` with the virtual environment active:

```
python manage.py backend_status --sources        # what is configured
python manage.py news_report                     # counts per category, newest dates, image rules
python manage.py configure_sources               # adds more categories + candidate sources (all OFF)
python manage.py fetch_news --source 1 --dry-run # test a source, writes nothing
python manage.py fetch_news --source 1           # real fetch
```
New sources are created **disabled and unapproved**. Switch one on in the admin (`News sources`) only after you have checked the publisher's terms: tick *Rights confirmed* and *Enabled*.
Fetched stories are drafts until an editor publishes them, unless a source is marked *Trusted* and *Auto publish*.
Full workflow, limits and NewsAPI quota: **docs/NEWS.md**.

## 5. Why images are not showing, and what to do

Images are **blocked by default** for every source. A publisher's picture is only used if the source has both **Allow images** ticked and the picture's exact host name listed in **Image hosts**. Your BBC sources have neither, so no BBC picture is ever stored. That is a rights setting, not a bug.

Your options, from simplest:

1. **Check your permission.** If your agreement with the publisher covers their pictures, edit the source in the admin: tick *Allow images* and add the host (for BBC feeds: `ichef.bbci.co.uk`). Then fetch again, and for stories you already have run `python manage.py backfill_images --source 1` (dry run) and then `--apply`. BBC feed pictures are small (240 px wide), so they look soft on the large cards.
2. **Use your own pictures.** In the admin, open an article, copy your image into `backend/media/` and fill **Image path** (for example `2026/10/photo.jpg`) plus **Image credit**. You own these, so no rule applies.
3. **Use sources with open or licensed images** (for example government press offices or Creative Commons collections), after reading their licence, and add them with *Allow images* on.
4. **Do nothing.** Cards without a picture show the NexusUp placeholder and still look tidy.

The site never rewrites picture links, never guesses a picture, and never copies an image from a page it was not given.

## 6. Looks: themes and dark mode

The header has a **Light / Dark / Auto** switch (Auto follows your computer) and a **Color Theme** menu with six palettes:
Royal Indigo, Crimson Ember, Teal Wave, Forest Lime, Amber Sunrise and Rose Magenta. Each palette has its own light and dark version, and the choice is remembered in the browser.
Colours live in one file: `frontend/src/services/themes.js`; the styling in `frontend/src/styles/site.css` (bottom section, "Design layer").

## 7. Translation

Off by default. Set `TRANSLATION_PROVIDER` in `backend/.env` to `libre` (your own LibreTranslate server) or `google` (needs `TRANSLATION_API_KEY`, billed per character). Keys stay on the server. Originals always remain available. Details and limits: **docs/NEWS.md**.

## 8. Tests

```
cd backend  && python manage.py test apps.news         # backend (uses a temporary test database)
cd frontend && npm test                                 # quick unit tests
cd frontend && npm run build                            # production build check
cd frontend && npm run dev   # then in another terminal:  npm run test:browser   (Playwright)
```
First time for browser tests: `npx playwright install chromium`. More in **docs/TESTING.md**.

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen PowerShell |
| `docker: command not found` / cannot connect to daemon | Start Docker Desktop and wait until it says *running* |
| Port 3306 already in use | Set `DB_PORT=3307` in `database/.env` and `backend/.env`, then run `up` again |
| `Access denied for user` | Passwords in `backend/.env` and `database/.env` differ. If you changed `database/.env` after the first start, run `db reset` once |
| Site is empty | Run `news_report`; fetch a source, then publish drafts in the admin |
| Blank page at :5173 | Backend not running on port 8000 |
| Unicode / Hindi text looks wrong in MariaDB | The compose file already uses `utf8mb4`; do not create the database by hand |

## 10. Safety rules built in

Fetching is manual; sources start disabled; only approved image hosts are used; secrets stay in `.env` files that Git ignores; original SQLite files are never modified by the scripts; imports refuse to overwrite existing articles.

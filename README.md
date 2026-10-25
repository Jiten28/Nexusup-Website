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

## 4. Getting news (from the admin, no commands needed)

Open **http://127.0.0.1:8000/admin/** → **News sources**.

1. Click **Add recommended sources** (top right). This creates the categories and a list of BBC section feeds. They start switched off.
2. Tick the sources you want (for example *BBC News: India* and *BBC News: World*). In the **Action** menu choose **1. Approve** and press *Go*.
   Approve means: *"I have permission to use these feeds."* It enables the source, confirms rights and allows the picture hosts that the feed itself uses.
3. Tick them again, choose **2. Fetch now**, press *Go*. The green message tells you how many stories were saved. Text, summary and picture links are saved together.
4. Open **Articles**, tick the drafts, choose **Publish selected articles now**. Or, once you trust a source, choose **3. Publish new stories from these sources automatically**.
5. **Fetch runs** shows every fetch with counts and any error.

Fetching needs `NEWS_FETCH_ENABLED=1` in `backend/.env` (the example file already has it). If the page shows an empty list or a warning, restart the server after changing `.env`.

Nothing is fetched while visitors browse, and nothing is fetched on a timer. The same steps as commands (from `backend`, virtual environment active):
```
python manage.py configure_sources              # = "Add recommended sources"
python manage.py fetch_news --source 1 --dry-run
python manage.py fetch_news --source 1
python manage.py news_report                    # counts per category, newest dates, image rules
```
Only approve a feed after you have read the publisher's terms. More detail, limits and NewsAPI quota: **docs/NEWS.md**.

### How much text and which pictures do I get?

* A feed gives what the publisher puts in it: headline, date, a short summary, a link and usually a small picture. Many publishers (BBC included) do **not** put the full article in the feed, so the site shows the summary and a clear "Read the original" button. It never pretends a summary is the full article, and it does not copy text from the publisher's web page.
* If a feed does include full text (`content:encoded`), the site saves and shows it automatically.
* For full articles and large pictures, use feeds whose licence allows it (your own content, press-office feeds, Creative Commons or licensed news APIs) and add them as a source in the admin (*Add news source*; adapter *rss*).

## 5. Why images are not showing, and what to do

Images are **blocked by default** for every source. A publisher's picture is only used if the source has both **Allow images** ticked and the picture's exact host name listed in **Image hosts**. Until a source is approved, no picture is stored. That is a rights setting, not a bug.

Your options, from simplest:

1. **Check your permission.** (If stories were fetched before pictures were allowed: in News sources tick the source and choose **2b. Get pictures for stories already saved**.) If your agreement with the publisher covers their pictures, use the admin action **1. Approve**: it ticks *Allow images* and fills *Image hosts* from the feed itself (for BBC: `ichef.bbci.co.uk`). Then **2. Fetch now**; for stories you already have run `python manage.py backfill_images --source 1` (dry run) and then `--apply`. BBC feed pictures are small (240 px wide), so they look soft on the large cards.
2. **Use your own pictures.** In the admin, open an article, copy your image into `backend/media/` and fill **Image path** (for example `2026/10/photo.jpg`) plus **Image credit**. You own these, so no rule applies.
3. **Use sources with open or licensed images** (for example government press offices or Creative Commons collections), after reading their licence, and add them with *Allow images* on.
4. **Do nothing.** Cards without a picture show the NexusUp placeholder and still look tidy.

The site never rewrites picture links, never guesses a picture, and never copies an image from a page it was not given.

## 6. Looks: themes and dark mode

The header has a **Light / Dark / Auto** switch (Auto follows your computer) and a one-click **Color Theme** button that moves to the next of eight palettes:
Graphite Silver, Emerald Imperial, Ruby Velvet, Amethyst Noir, Arctic Aurora, Copper Sunset, Midnight Rose and Ocean Navy (eight, with smooth same-colour gradients). Each palette has its own light and dark version, and the choice is remembered in the browser.
Colours live in one file: `frontend/src/services/themes.js`; the styling in `frontend/src/styles/site.css` (bottom section, "Design layer").

## 7. Translation (free, runs on your computer)

The "Read in" menu at the top translates the menus and the stories on the page. It uses **LibreTranslate**, a free translation server that runs in Docker, so no text leaves your machine and nothing is billed.

1. Start it (first start downloads the language models: a few minutes, internet needed):
   `docker compose -f backend/translate/compose.yaml up -d`
2. In `backend/.env` set `TRANSLATION_PROVIDER=libre` (the address `http://127.0.0.1:5000` is already the default) and restart the backend.
3. Check it: `python manage.py doctor`. The *Translation* section should list the languages, and the site's menu then shows them.

Languages are chosen in `backend/translate/compose.yaml` (`LT_LOAD_ONLY`; Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Urdu, Arabic, Spanish, French, German, Portuguese, Russian, Japanese, Chinese are included). Originals always stay available (choose *Original · English*).
Limits: about the first 24 stories on a page are translated; stories added with Load More stay English until you pick the language again; requests are rate-limited per visitor. Machine translation can be wrong, so the site labels it.
Paid option: `TRANSLATION_PROVIDER=google` with `TRANSLATION_API_KEY` (billed per character). Keys stay on the server.

## 7b. Something not working? Run the doctor

```
python manage.py doctor                  # checks database, sources, pictures, stories, translation
python manage.py doctor --check-images   # also tests 3 stored picture links
```
It prints what is wrong in plain words and the exact next step. It only reads; it changes nothing and never prints keys.

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
| `ImportError ... cannot import name 'unescape'` when fetching | Fixed in this version (`apps/news/ingestion.py`). Replace your `backend` folder files with the new ones and restart `runserver` |
| Site opened from a phone or another PC (for example `http://192.168.1.235:5173`) says *Stories are temporarily unavailable*, or RSS feed / Sitemap show an error | Fixed: the dev server now forwards requests as Django's own address, and Django (in `DJANGO_DEBUG=1`) accepts this computer's network IPs. Restart **both** `runserver` and `npm run dev`. Set `DEV_ALLOW_LAN=0` in `backend/.env` to turn it off |
| *Fetch runs* page is empty | A fetch has not completed yet. Use *News sources → 2. Fetch now*; every attempt that gets past the checks is listed under *Fetch runs* |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen PowerShell |
| `docker: command not found` / cannot connect to daemon | Start Docker Desktop and wait until it says *running* |
| Port 3306 already in use | Set `DB_PORT=3307` in `database/.env` and `backend/.env`, then run `up` again |
| `Access denied for user` | Passwords in `backend/.env` and `database/.env` differ. If you changed `database/.env` after the first start, run `db reset` once |
| Site is empty | Run `news_report`; fetch a source, then publish drafts in the admin |
| Blank page at :5173 | Backend not running on port 8000 |
| Unicode / Hindi text looks wrong in MariaDB | The compose file already uses `utf8mb4`; do not create the database by hand |

## 10. Safety rules built in

Fetching is manual; sources start disabled; only approved image hosts are used; secrets stay in `.env` files that Git ignores; original SQLite files are never modified by the scripts; imports refuse to overwrite existing articles.

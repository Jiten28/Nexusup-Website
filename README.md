# NexusUp — separate Django redesign

**Start with [docs/AUDIT.md](docs/AUDIT.md).** It was completed before application implementation. Full ZIP listings and scope limits are included alongside it.

This is a working local demonstration, not a production deployment or migrated website. All 10 seeded articles are **new, illustrative sample content**. No production database was supplied, discovered or copied. No live site was modified. No production services are connected.

## Quick start (Python 3.10+; tested on Python 3.13)

From this folder on Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Open **http://127.0.0.1:8000/** on the same computer. Or run `sh scripts/run_demo.sh`. The server intentionally binds only to loopback. Stop with Ctrl+C. Nothing is deployed. First-time setup needs access to a Python package index. Windows: `py -m venv .venv`, then `.venv\Scripts\activate`; use the same `python` commands. Do not run the shell script on Windows.

The packaged `demo.sqlite3` contains only samples; running migrate/seed again is safe and does not overwrite article edits. You can delete it and rerun both commands for a clean local reset. The example author has an unusable password and cannot sign in. No administrator credentials are shipped.

### Editorial workflow

```sh
python manage.py createsuperuser
```

Choose credentials interactively on your machine; then open `/admin/`. Add a category/article, set the author, write plain-text paragraphs, choose a relative media path and meaningful image alt/credit. Drafts and future-dated posts are not public. Set status Published and a publication time at or before now to show it. Leave sample status on for demo work. Review comments under Comments and approve intentionally. Contact messages stay in the database; no email is sent. Delete fictional submissions after testing.

## Stack and features completed
- Python/Django ORM with migrations; Django templates, hand-written HTML/CSS and vanilla JS. No PHP, WordPress templates/plugins, frontend framework, CDN or remote fonts in the application.
- Responsive editorial homepage; verified archive book logo plus new text wordmark; feature story, short list, category links and article cards.
- Search, category archives, pagination, empty states, article reading pages and related articles.
- Accessible labels, skip link, visible keyboard focus, reduced-motion handling, responsive menu (Escape closes), system-aware dark mode with browser-local preference.
- Per-story save toggle in the current browser (no account sync or saved-stories index); copy-link action with failure feedback.
- Admin draft/publish workflow; moderated comments; local contact storage; CSRF-protected forms, server validation and a basic **demo-only** per-session throttle/honeypot.
- Canonical/Open Graph tags, XML sitemap and RSS feed; robots and meta tags deliberately prevent demo indexing. Plain-text content is escaped, not rendered as arbitrary HTML.
- Seven reference raster images retain exact year/month upload paths. One verified book logo is bundled separately. `docs/media-manifest.json` provides hashes and rights caveats.
- Local legacy media alias `/wp-content/uploads/<path>` for supplied media, plus `/media/<path>`. Production alias must be configured at the web server/CDN after review.
- Inactive advertising space; `/ads.txt` disabled by default. Exact original declaration in `docs/reference-ads.txt`. `ADS_TXT_ENABLED=1` explicitly opts in to serving that declaration, **not** to loading ads. No advertising scripts are implemented.

## Test and inspection

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

See `docs/TESTING.md` and the included test log for actual results and limits. Browser QA was performed locally, not against production. Both CSS and JS are entirely local.

## Database boundaries / MariaDB

`news/models.py` and `news/migrations/0001_initial.py` define a **new proposed schema**: Category, Article, Comment, ContactMessage, plus Django's authentication/session tables. This is not an inferred WordPress or existing production schema. The WordPress ID field is an empty future mapping aid, not a migrated ID.

Local demo uses SQLite only. Production settings require `DB_ENGINE=mariadb` and Django's MySQL backend, with `utf8mb4`, strict SQL mode and environment-supplied credentials. Install `requirements-production.txt` in a separate environment. mysqlclient requires Python build tools, pkg-config and MariaDB/MySQL client development headers (e.g. `default-libmysqlclient-dev` on Debian/Ubuntu). Use an approved, supported MariaDB release compatible with your pinned Django; MariaDB 10.11 LTS or newer is a reasonable validation target. **MariaDB execution has not been tested in this sandbox.**

Copy `.env.example` to `.env` if helpful and set real values privately. The app does not auto-load dotenv files: export variables in the shell, via your process manager, or, for a trusted local file only, `set -a; . ./.env; set +a`. Never commit secrets. `DJANGO_DEBUG=0` fails fast without a secret, MariaDB configuration and approved HTTPS SITE_URL.

**Do not run migrations against an existing WordPress database.** After explicit authorization, provision a separate Django database and least-privilege account in isolated staging, take backups, test the ORM and migration suite there, then apply app migrations to that new database. See `docs/MIGRATION_PLAN.md` for the content migration gates.

For an eventual authorized deployment, Gunicorn would serve `config.wsgi:application` behind a correctly configured HTTPS reverse proxy, with `collectstatic` output and vetted media served separately. This is documentation, not a deployment. No container, service or infrastructure has been started or provisioned. Configure proxy trust only for a real trusted proxy; it is intentionally not assumed here.

## Media restoration (optional, local only)

The complete archive is not duplicated in this lightweight package. Keep the uploaded ZIP as your untouched reference. The full inventory covers all its members. To evaluate copying more date-organized raster media locally:

```sh
python scripts/restore_media.py /path/to/NexusUp_Redesign.zip
# Inspect the dry-run result first. Then, if desired:
python scripts/restore_media.py /path/to/NexusUp_Redesign.zip --apply
```

This verifies candidate paths, CRC and hashes; never overwrites conflicting files; excludes PHP, SVG, HTML, plugin caches, schema-generated folders and non-dated uploads. Paths stay `YYYY/MM/filename`. It does not migrate captions/alt text/credits, rewrite content or identify duplicate media by meaning. Validate file signatures, rights and malware scan separately before public serving. It is an opt-in local filesystem helper, not a content importer.

## Known limitations / not completed
- No real articles, users, passwords, categories, comments, settings or SEO/redirect data imported. No production-schema analysis. No existing URL-parity guarantee.
- No real translation, analytics, advertising delivery, SMTP, automatic syndication, subscription system, live scores, commerce or off-site backups. No cookies are implied for these disabled providers.
- WP Mail SMTP reference directory is incomplete. No reference plugin is installed in Django, and plugin activation/licensing/complete behavior is unknown.
- Editorial pages use plain text, not a rich-text CMS or arbitrary media uploads. No drag-and-drop page builder; no full-text search index, nested category taxonomy, tags, author archive or automated WP importer yet.
- Anti-abuse controls are demonstration-grade, session-based and in-memory; they can be bypassed and do not span workers. Add shared rate limits, production monitoring, retention/deletion controls and moderation procedures before enabling public submissions.
- Browser-local saves are not a user account feature. Clipboard availability depends on the browser/secure context. Demo privacy/terms text is not legal sign-off.
- Reference photographs, logo and any fonts require rights review before publication. No claim of ownership or rights clearance. System fonts are used; supplied Italiana/plugin fonts are not copied.
- Production MariaDB, reverse proxy, email, ad/consent compliance, real migration fidelity, load testing, comprehensive security audit and assistive-technology testing remain outstanding.

See `docs/IMPLEMENTATION.md`, `docs/MIGRATION_PLAN.md`, `docs/TESTING.md` and `docs/AUDIT.md` for the detailed handoff. No deployment is authorized by this deliverable.

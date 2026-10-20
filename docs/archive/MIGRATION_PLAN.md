# Safe WordPress migration plan — pending real source data

**No content migration has occurred.** Source tables, their prefix, custom columns, row counts, relations, collation and plugin option formats are unknown. The Django schema is a proposed target, not a reverse-engineered source. Do not connect this demo to production or point Django migrations at WordPress.

## Gate 1 — source collection and explicit scope approval
1. Preserve immutable copies and checksums of this uploaded ZIP, a consistent sanitized database export and a complete original media snapshot. Encrypt backups at rest and restrict access.
2. Request either an actual SQL/schema snapshot and a staging restore, or WXR with supplementary settings/SEO/menu/widget/redirect/media exports. WXR alone will not capture every plugin setting, role or option.
3. Obtain active theme/child theme/plugins, actual permalink structure, site URLs/timezone, menus, widget assignments, redirects, taxonomies, custom fields, authors/roles and block/page-builder usage. Confirm whether any private posts or personal data may be processed.
4. Confirm publishing workflow, corrections, comment moderation, contact retention, translation requirements, ad/analytics consent and licensed use of automated/syndicated content. Plugin directories are not approved requirements.
5. Confirm the verified book logo remains desired. Obtain master brand assets, original image credits/rights and any licensed fonts. Treat schema-generated thumbnails as derivatives, not authoritative originals.

## Gate 2 — inspect the actual source, then approve mapping
On an isolated restore, inspect table definitions, actual relationships, counts and plugin fields first. Record exact discovered names; do not assume `wp_`, an unmodified schema or fields inferred from filenames. Create a reviewed mapping document before importer code.

Candidate mapping concerns (not a discovered schema):
- Posts/pages → target article or appropriate standalone page; preserve draft/private/future status, slugs, excerpts, dates, edited dates, source IDs and authors. Support WordPress local/GMT date distinctions explicitly.
- Taxonomies → categories/tags after inspecting hierarchies and term relationships. Current demo categories are only proposals. Decide whether tags, nested categories and article multi-category membership are required before finalizing target schema.
- Users → separate identity map. Do not copy WordPress password hashes into Django authentication. Decide attribution-only accounts vs active logins; require secure resets and reviewed role mapping.
- Body content → parse blocks/shortcodes/page-builder structures in staging; sanitize allowlisted output. Current demo stores escaped plain text. Decide on a safe rich-text/content-block model before real import; do not flatten real production formatting silently. Never execute shortcodes or embed PHP.
- Media → authoritative attachment metadata to original files, derivative sizes, captions, alt, credit and rights. Preserve year/month paths where valid. Validate hashes, MIME signatures, duplicates, names/case/Unicode and collision handling. Disallow active content and server execution. Do not blindly copy caches or provider uploads into public storage.
- SEO → inspect actual SiteSEO/Yoast metadata and choose the authoritative source when values conflict; preserve canonical URLs, titles, descriptions, social images and schema only after validation. Review generated schema semantically; no invented news claims.
- Comments → preserve approved/pending/spam status, hierarchy, source IDs, dates and attribution. Target currently has a simple flat moderated model; extend it if verified threads need preservation. Minimize personal data, do not import private email/IP fields by default.
- Redirects → export and review plugin/server rules. Build an explicit old→new map with constraints against loops, chains, open redirects and collisions. Current app has NO article redirect importer.
- Settings/integrations → reimplement approved behavior with native Django or approved providers, never port plugin PHP or provider secrets. Reauthorize providers only through approved secure flows.

## Gate 3 — dry-run importer on an isolated staging copy
Build importer only after the mapping is signed off. It should be repeatable, non-destructive, resumable and support a read-only dry run. Use ORM writes, transactions/batches, external-ID uniqueness and a migration ledger for every entity. Fail explicitly on missing authors/media, duplicate slugs or unknown structures; never silently drop records. Produce per-type counts, mismatch reports and rejected-item lists. Keep original IDs separate from Django PKs.

The optional `scripts/restore_media.py` is only a local raster-file helper, not that importer. Its default is dry run; it preserves dated paths and refuses conflicting files. Review the complete archive separately for other approved assets. It deliberately excludes schema-generated uploads, caches, SVG, scripts and non-dated files.

## Gate 4 — verify MariaDB and reconciliation
Create a NEW, isolated Django MariaDB database with a least-privilege user. Install mysqlclient; test migrations with utf8mb4/strict mode, indexes, unique/null behavior, UTC/timezone handling and rollback/restore. The SQLite suite is not proof of MariaDB correctness. Add database-specific tests and run them on an authorized disposable database; Django test execution creates/deletes a test database, so grant only that scoped access.

Reconcile counts by type/status/category/author/date; verify legacy IDs and media hashes. Sample long bodies, non-English text, emoji, embeds, shortcode conversions, comments, empty fields and missing media. Crawl old and new staging URLs; validate status codes, redirect maps, canonical/social tags, structured data, feed, sitemap, internal links, accessibility and performance. Obtain editorial sign-off and verify no sample content or false credits remain.

## Gate 5 — launch only with separate explicit approval
Take final backups, rehearse restore, agree a content freeze/delta import, define rollback criteria and ownership. Configure static/media serving, legacy media alias, domain/TLS, robots/indexing, mail, consent, caching, monitoring and backups in staging. Replace demo legal text and satisfy rights/privacy review. Remove the demo banner/noindex only after authorized launch readiness review. Switch production routing/DNS only under explicit user approval; this package grants none.

Rollback: keep old WordPress intact/readable during the agreed window; retain immutable export, media and source→target manifests; reverse routing according to the approved runbook if acceptance checks fail. Do not rely on destructive importer reversal as the sole rollback path.

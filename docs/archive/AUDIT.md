> **Historical baseline document.** This describes the previous demo. For this incremental enhancement, use `ENHANCEMENT_REPORT.md`, `INTEGRATIONS.md` and `enhancement/` test evidence.

# NexusUp reference audit — before implementation

Audit date: 18 October 2026. Scope: uploaded NexusUp_Redesign.zip and a read-only retrieval of https://nexusup.in/. No production logins, writes, database connections, service calls or deployment were performed.

## 1. Access and inventory
- ZIP: 449,110,837 bytes (428.3 MiB); 21,434 entries, 19,920 files; 535,807,366 uncompressed bytes.
- All member paths were checked for traversal, absolute paths and symbolic links; none rejected. No encrypted entries. Full ZIP CRC test passed. All members extracted successfully to an isolated reference directory. No PHP was executed.
- Exact complete file listing: archive-contents.txt. Machine-readable path/size/compressed-size inventory: archive-inventory.json.
- Accessible: ads.txt; wp-content/themes/digital-newspaper (152 files); wp-content/plugins (13,441 files across 11 directories); wp-content/uploads (6,326 files).
- wp-content contains those three directories. WordPress core, wp-config.php, a database dump and WXR content export are NOT included. No .sql, .gz or .wxr file was found. Plugin XML files are not a content export.
- Uploads include 2025/08, 09, 10, 12; 2026/01 through 07; fonts; schema-and-structured-data-for-wp; tkk.cache; wpconsent; wpforms; wpseo-redirects. The inventory is authoritative for exact paths.

## 2. Verified theme and visual assets
- Theme header: Digital Newspaper by BlazeThemes, version 1.1.18. This is the sole supplied theme. Read-only live HTML also links its version 1.1.18 stylesheets, verifying it is used for the retrieved homepage.
- Inspected style.css header, functions.php, header/footer/search/single/archive/comments templates and selected inc/template-parts hooks. Code supports featured images and derivative image sizes, top/main/footer menus, custom logo, HTML5 search/comments, feeds, sidebars, customizable news blocks, ticker, sticky header, breadcrumbs, social links and reading-time elements. Theme code availability does not establish configured menus, ordering or widget contents.
- Logo candidates: uploads/2025/10/ext-custom-logo-1759738820627.webp and its 150x150 variant depict a dark open-book symbol. uploads/schema-and-structured-data-for-wp/sd-logo-white.png is a colorful website icon, not a confirmed NexusUp brand mark. Plugin vendor logos are not NexusUp assets. Live HTML identifies the open-book upload as its custom-logo with alt “Nexus Up”, verifying its current homepage use. No unambiguous NexusUp text wordmark was found by filename. Demo preserves the verified book mark alongside a newly typeset wordmark.
- Content font: uploads/fonts/italiana-latin-400-normal.woff2. Font Awesome icon fonts occur in the theme; Google Sans assets occur inside Site Kit. These files do not prove public-site typography or license clearance for redistribution. The demo uses system sans and system serif; no plugin font is repurposed.
- Media contact sheet visually inspected: cricket photography, team/player collages, finance screenshot/illustrations, one generic cartoon and logo candidates. Many repeated resized/converted derivatives; filenames sometimes end .webp.webp. Names alone are not reliable captions, dates or rights evidence. Demo imagery is reference-only, rights unverified; obtain clearance before public use.

## 3. Plugin directory findings (presence only)
| Directory | Header name | Version |
| --- | --- | --- |
| extendify | Extendify WordPress Onboarding and AI Assistant | 3.1.5 |
| google-site-kit | Site Kit by Google | 1.189.0 |
| gtranslate | GTranslate | 3.1.1 |
| hc-extendify-lc | Site Assistant | 1.0.0 |
| siteseo | SiteSEO - SEO Simplified | 1.4.1 |
| siteseo-pro | SiteSEO Pro | 1.4.1 |
| updraftplus | UpdraftPlus - Backup/Restore | 2.26.7.0 |
| wordpress-seo | Yoast SEO | 28.7 |
| wordpress-seo-premium | Yoast SEO Premium | 26.9 |
| wp-automatic | WordPress Automatic Plugin | 3.130.1 |
| wp-mail-smtp | Partial directory; bootstrap lacks plugin header | Unknown |

Installed-directory presence is verified; activation, licensing, authenticity, scheduled jobs and saved configuration are unknown. All 11 directories were inventoried; 10 plugin headers and the SMTP bootstrap were inspected. WP Mail SMTP is incomplete: its bootstrap references src/Core.php but no src directory is supplied. It cannot be treated as a complete restorable plugin. Other directory completeness has not been certified; not every PHP/JS/vendor file. No plugin security certification is implied.

## 4. Advertising and integrations
- Exact supplied ads.txt: `google.com, pub-4403090676624554, DIRECT, f08c47fec0942fa0`.
- This declares a Google publisher relationship; ownership, AdSense approval, active placement IDs, consent requirements and revenue configuration are NOT verified.
- Live homepage HTML includes a Google tag (GT-5MRC4LQH), a Google AdSense script with ca-pub-4403090676624554 and a GTranslate float script; these establish script inclusion, not provider/account validity, consent compliance or successful network execution. Site Kit additionally suggests Search Console integrations. WP Mail SMTP suggests outbound mail. WP Automatic suggests content automation. UpdraftPlus suggests backups. SiteSEO and Yoast directories suggest overlapping SEO capabilities. These are candidate workflows, not evidence they are active.
- uploads/wpconsent, wpforms, wpseo-redirects and schema-and-structured-data-for-wp are residual workflow evidence only. Corresponding active plugins/configurations cannot be inferred from upload folders.
- Demo must make zero advertising, analytics, translation, SMTP, syndication or backup-provider calls. Ads remain labeled placeholders. Publisher line retained as a reference and only served if explicitly opted in locally; no ad scripts included.

## 5. Read-only live-site observations
The extracted homepage title is “Nexus Up - Whats in”. It shows a news/article feed dominated by cricket: headings about Josh Hazlewood, Mohammad Aamir/Babar, Tilak Verma and other stories. Visible repeated metadata includes “Category 2”, author “Nexus”, relative age, comment count and 5–7 minute reading labels. Treat displayed dates/statements as site content, not independently fact-checked reporting. Live HTML also exposes navigation labels Home, Blogs, Business, Stock Market, Investments, Technology and Science; these labels are verified, while their targets/content coverage need a fuller crawl. Demo preserves these broad topic paths and adds a Cricket section to fit the observed feed. Extraction verifies these elements, not every live interaction or exact visual styling. Source: https://nexusup.in/ retrieved during this audit.

## 6. Preserve vs clarify
| Workflow | Evidence | Redesign disposition |
| --- | --- | --- |
| Article feed, category labels, author/date/read time | Verified homepage content and theme templates | Reimplement as Django list/category/detail pages with clearly labeled samples |
| Search, article archive, featured images, navigation | Verified theme support; actual settings unknown | Reimplement responsive navigation, search and paginated archives |
| Editorial publishing | WordPress content site + template support; user roles unknown | Proposed Django admin draft/publish flow, not imported roles |
| Comments | Comment metadata on homepage, theme comment template | Proposed moderated comments; legacy threads require export and policy confirmation |
| SEO/feed/breadcrumbs | Theme support + SEO plugin directories | Native canonical/social tags, sitemap, RSS and breadcrumbs; choose source metadata later |
| Translation, automation, SMTP, analytics, backups | Plugin presence only | Not connected; confirm business need, accounts, consent and source rights |
| Redirects and consent/forms | Upload residue only | Inventory and map later; demo contact storage is local and not emailed |
| Advertising | Supplied ads.txt only | Preserve exact reference; inert placements; approval required for live services |
| Accounts, commerce, subscriptions, live scores | Not established | Do not invent as existing features; no commerce or live-score integration |

## 7. Coverage and required additional material
Full inventory, CRC validation and extraction: ALL entries. Semantic inspection: theme header/functions and selected templates/hooks; plugin main headers; ads.txt; font names; representative media contact sheet and selected images. NOT inspected line-by-line: plugin/vendor implementations, every JSON/cache file, every image/derivative, every theme customizer setting; no source PHP executed. Full malware/license/security audit is out of scope. Archive size did not prevent access; content review is selective and explicitly scoped.

Needed for a faithful migration: sanitized WordPress SQL snapshot with actual table prefix/schema (or WXR plus attachment and settings exports), active theme/options/customizer/menu/widget exports, active-plugin list, permalink rules, taxonomies/authors/roles, custom fields, SEO metadata/redirect exports, comment policy and export, original media/alt/caption/credit mapping, analytics/ad/SMTP/translation requirements (NOT secrets in chat), approved logo/font/imagery rights and a staging rollback/launch plan. Inspect exports for private data before sharing.

## 8. Implementation boundary
Proceed with a separate Django application, new proposed ORM schema, sample seed data and local SQLite demo. Production configuration will target MariaDB through Django's MySQL backend. No claim of production schema discovery or content migration. No PHP templates/plugins or provider credentials will enter the app. Original media year/month paths will be retained for a selected demo subset; full media remains in the user-supplied archive. No deployment authorized.

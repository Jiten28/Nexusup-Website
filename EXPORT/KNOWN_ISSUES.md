# Export status and known limitations

This is the current `/data/NexusUp` workspace snapshot, not a download from the user's Windows installation.
The active Windows server/project/database has not been matched to this copy.
No pending backend or carousel fixes were implemented during the recent audit-only turns.
No live fetch, source activation, automatic publication or deployment was performed for this export.

Known implementation limitations retained intentionally:
- NewsSourceAdmin has no manual fetch action.
- The fetch command enforces NEWS_FETCH_ENABLED; ingest() itself does not yet enforce it.
- Blocked/deferred paths may have no FetchRun record; a rollback may leave an overstated imported count in the failed run.
- The optional Compose ingestion profile hardcodes NEWS_FETCH_ENABLED=1. Do not activate it.
- Carousel autoplay starts OFF and resets OFF when story identities change.
- Hover/focus pause is active; Play may remain interaction-paused while a control retains focus.
- Desktop/tablet carousel image minimum heights remain around 350/360 px. Compact styling is not implemented.
- Normal frontend mode is API-driven. Explicit demo mode can substitute clearly labeled frontend fixtures.
- Existing database articles are clearly labeled samples, not real-news ingestion results.

Historical docs may describe older packages containing build outputs/recovery archives. The EXPORT/OMISSIONS.md
and EXPORT/MANIFEST.json in this export are authoritative for its actual contents.
Historical test/verification claims are not a statement that tests were rerun for this export.

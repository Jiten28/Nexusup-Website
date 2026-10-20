# Executed QA evidence

Final Django tests run via the local Python 3.13/Django 5.2.18 environment. Browser tests used Playwright 1.50.0 from the preinstalled Python package driver with /usr/local/bin/chromium, local loopback only. For reproduction, use the portable scripts/enhancement_qa.cjs with npm playwright and a Chromium executable. supplemental.cjs records the exact sandbox supplement (adapt its paths for another machine).

Provider smoke tests are separate read-only public requests, not browser fixtures or persisted imports. All integrations remain disabled in packaged settings/database. Preview widget success states marked QA fixture are deterministic simulated data. The original historical docs/previews directory is retained; use the PNGs in this folder for the new design.

# Testing
```
cd backend && python manage.py test apps.news
cd backend && set PYTHONPATH=. && python -m unittest apps.news.tests_images
cd frontend && npm install && npm test                 # node unit tests
cd frontend && npm run build
cd frontend && npm run dev                              # then, in another terminal:
npm run test:browser   # needs QA_BASE_URL=http://localhost:5173 ; screenshots go to docs/verification/acceptance
```
`test:browser` mocks `/api/*` and publisher images; it proves front-end behaviour only. Verify live data with `news_report` and by opening the site.

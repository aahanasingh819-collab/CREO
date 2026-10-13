# Phase 3 delivery — 13 October 2026

Phase 3 is implemented on top of the existing Phase 1 and 2 application. Existing environment configuration and marketplace data were preserved.

## Completed

- Private evidence submission for a specific portfolio claim, with validated image uploads or HTTPS evidence links, ownership checks, withdrawal, staff permission checks, review rationale, and public trust labels.
- Admin Reviewed applies only to a current project revision. An incrementing database version invalidates approval after edits, including rapid edits with identical timestamps. Reviewers cannot approve their own claims or fictional demo work. Signals do not certify identity, quality, or usage rights.
- Brand invitations from brief matches, explicit consent to share the brief, participant-only engagement pages, and an immutable shared brief snapshot. One invitation per brief/creator prevents duplicate submissions.
- Accept/decline, start, submit an HTTPS delivery link, request revision, complete, and cancel actions. Role and state checks run server-side; version-conditional updates reject stale submissions. Activity events are appended atomically. Briefs with engagement history are protected from deletion and can be archived.
- Consistent navigation to engagement inboxes, creator evidence, and staff review queues; styled forms, timeline, empty states, and reuse of the responsive design system. Evidence queries are batched and the public creator detail reuses prefetched projects.
- Production Waitress entry point, WhiteNoise static collection, non-root Docker configuration, persistent media configuration, database health endpoint, and separate SQLite/PostgreSQL CI jobs. Public image streaming checks visible portfolio records; private evidence has authenticated download routes with no-store caching.
- Preserved 14 labelled fictional creators and 28 demo projects. Added an idempotent, explicit `seed_showcase --brand USERNAME` command for two fictional briefs in a selected existing brand account. It sends no invitations and preserves edits.
- Deployment instructions, architecture diagram, and six-minute presentation guide for the five-person team.

## Verification performed

| Check | Result |
| --- | --- |
| Full Django suite, final run | **90 tests passed**, SQLite, 29.145 seconds |
| Django system checks | No issues |
| New migrations | Applied successfully to local SQLite |
| Migration drift | No changes detected after generated migrations |
| Production static collection | Successful; 529 files post-processed |
| Production-settings Django client smoke | Landing page, directory, health, login, and existing portfolio image returned 200 |
| Production deploy checks | No errors; two intentional HSTS policy warnings described below |
| Catalog inspection | 14 fictional creators, 28 labelled projects |

The suite includes prior authentication, ownership, upload, brief generation, filtering, matching, comparison, and CSRF tests. Phase 3 adds participant isolation, snapshot immutability, invitation idempotency, stale transition rejection, submission validation, revision/completion history, protected deletion, evidence review permissions, private downloads, stale approval invalidation, and showcase seed preservation. Temporary test-media access required running tests outside the restrictive execution sandbox.

Two failures discovered during development were fixed: private storage tests initially retained a cached field-storage object, and timestamp-only revision checks could miss rapid edits on Windows. Review validity now uses an incrementing version. Adding trust evidence also increased the fixed matching query bound from nine to ten queries, independent of catalog size.

## Run locally

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py runserver
```

Register your own creator and brand accounts, then optionally run:

```powershell
.venv\Scripts\python.exe manage.py seed_showcase --brand YOUR_BRAND_USERNAME
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py test
```

Use [DEMO_GUIDE.md](DEMO_GUIDE.md) for the end-to-end presentation and architecture. Use [DEPLOYMENT.md](DEPLOYMENT.md) for PostgreSQL, Replit, Docker, HTTPS, and persistent storage setup.

## Limits and unverified items

- PostgreSQL concurrency, GitHub Actions execution, Docker build/run, and real hosted deployment were not tested here. Their configurations are included; SQLite is the verified local fallback.
- No live Gemini request was made. Tests cover mocked responses and the offline fallback; actual free-tier credentials and eligibility remain operator configuration.
- Browser access became unavailable under the browser tool's security policy during the preceding phase. Phase 3 was verified through Django request/integration tests and template rendering, not a new visual browser inspection. A final desktop/mobile visual pass is still recommended before presenting.
- `check --deploy` reports W005 (HSTS across subdomains) and W021 (preload). These remain intentionally disabled without a configured domain policy; HTTPS redirects, secure cookies, and HSTS for the app's own host are enabled with debug off.
- The optional comparative test-shot feature was omitted to keep the required trust and engagement workflows reliable. Comparison remains the working Phase 2 capability.
- Engagement events are immutable through app routes, not a tamper-proof audit log. Only the latest delivery link is retained. No email, payments, binding contracts, or live chat are implemented.
- Evidence is a human review of a submitted claim, not automated forensic or legal verification. External proof links are opened manually and never fetched by the server.
- Hosted backup/retention, orphan upload cleanup, password recovery delivery, and large-scale abuse controls remain operational work, as detailed in the deployment guide.

No services were deployed and no external messages were sent.

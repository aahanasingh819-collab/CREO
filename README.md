# CREO

A Django marketplace for AI creators and brands. Phases 1�3 include creator portfolios, brand briefs, optional Gemini drafting, filtered discovery, explainable matching, comparison, private evidence review, and invitation-to-delivery engagement tracking. The local starter and all marketplace features work without an AI API key.

## Quick start

Python 3.11+ is required (tested with Python 3.12). From the project directory:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Copy .env.example to .env ONLY if you do not already have .env.
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

On macOS/Linux: `python3 -m venv .venv`, then `source .venv/bin/activate`; remaining commands are the same. If Windows activation is unavailable, use `.venv\Scripts\python.exe` directly.

Open http://127.0.0.1:8000. Register a creator to edit a profile and publish work, or register a brand to write briefs, rank matches, and compare creators. Seeded accounts deliberately have **unusable passwords**; register your own account rather than using shared credentials. `python manage.py createsuperuser` creates an administrator.

The local virtual environment in this workspace was created with Codex’s bundled Python because `python` was not on PATH. It can be used directly with `.venv\Scripts\python.exe manage.py runserver`. Virtual environments are machine-specific and ignored by Git.

## Configuration

Existing `.env` is preserved. The app loads `.env` without replacing real environment variables. Settings use `DJANGO_` names to avoid colliding with unrelated services.

| Variable | Behavior |
| --- | --- |
| `DJANGO_DEBUG` | Defaults to `True` for the local prototype |
| `DJANGO_SECRET_KEY` | Required when debug is off; development-only fallback otherwise |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts, without schemes |
| `DATABASE_URL` | PostgreSQL connection URL; omitted means SQLite |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins for hosted use |
| `REPLIT_DEV_DOMAIN` | Automatically added to allowed hosts and CSRF origins |
| `GEMINI_API_KEY` | Optional server-only key; never sent to the browser |
| `GEMINI_FREE_TIER_CONFIRMED` | Defaults to `False`; enable only for a project kept on the free tier |
| `GEMINI_MODEL` | Defaults to `gemini-3.5-flash-lite`; also permits `gemini-3.8-flash` |

### Gemini brief builder

Use a Google AI Studio project kept on the **free tier**, without enabling paid billing. Set `GEMINI_API_KEY` in `.env` or Replit Secrets, and set `GEMINI_FREE_TIER_CONFIRMED=True` after checking your project's tier. CREO cannot independently verify billing status: this flag is an operator acknowledgement, not a billing control. The builder makes one bounded REST request, never retries automatically, and never switches to a paid model or another provider.

The adapter uses Google's [structured JSON output API](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en). The allowed models were listed with free-tier text input/output in the [Gemini pricing documentation](https://ai.google.dev/gemini-api/docs/pricing) on 13 October 2026. Availability and quotas can change; check those pages before enabling it.

Brands explicitly choose Gemini and consent to sending their idea. Only the entered idea and schema instructions are sent; account data and saved briefs are not. Free-tier input may be used by Google to improve its products, so the UI asks for non-confidential ideas. Limits are 10 attempts per account per local calendar day and a 30-second cooldown, enforced by conditional database updates. Provider failures consume an attempt to prevent retry storms.

Generated JSON is validated again on the server for field names, types, enums, text lengths, positive ordered budgets, and valid future dates. Missing details remain blank for review. Nothing becomes a Brief until the brand edits and saves the standard validated form. API outages, invalid output, missing configuration, and quota exhaustion preserve the idea and offer a clearly labeled **local starter template**; this template is not presented as AI generation.

Gemini is not configured in the delivered local environment. The adapter is tested with mocked provider responses; a live Gemini request has not been verified.

### PostgreSQL

Create a PostgreSQL database and user through your host, then set:

```dotenv
DATABASE_URL=postgresql://creo:YOUR_PASSWORD@localhost:5432/creo
```

Use `?sslmode=require` when required by your database provider. Run `python manage.py migrate` and `python manage.py seed_demo` against the new database. Switching URLs does not transfer SQLite data. PostgreSQL is configured through `dj-database-url` and psycopg; this environment was verified with SQLite, not a running PostgreSQL service.

### Replit

1. Import this repository into a Python Repl.
2. Install requirements with `python -m pip install -r requirements.txt`.
3. Set a random `DJANGO_SECRET_KEY` in Replit Secrets. The development domain is discovered automatically.
4. Run `python manage.py seed_demo` after the first migration (or run `python manage.py migrate` first).
5. The Run button executes migrations and serves on `0.0.0.0:3000` through `.replit`.

This is a development/demo configuration, not a production deployment. Real deployments need durable database and media storage, HTTPS/proxy configuration, backups, and rate limiting. When debug is off, Django does not serve uploaded media; configure your host to serve `MEDIA_ROOT` safely. WhiteNoise handles **static** assets only. Replit hosting was not available for verification.

## Frontend

Django templates render every page. Tailwind 3 utilities are compiled and committed to `static/css/tailwind.css`; the semantic design system is in `static/css/site.css` and `static/css/phase2.css`. HTMX updates filtered search results and browser history. Alpine handles mobile navigation, the generation loading state, and consent-based video embeds. Forms, pagination, search, authentication, comparison, and CRUD work without JavaScript; video links provide a no-JavaScript alternative. All runtime styles, scripts, and demo images are local.

Optional CSS rebuild (Node is a **build tool only**, never the application backend):

```sh
npm exec --yes --package=tailwindcss@3.4.17 -- tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.css --minify
```

## Architecture

```text
config/       Settings, URLs, WSGI/ASGI
accounts/     Custom User, registration, role-aware workspace entry
creators/     Profile and normalized Tool / Skill / Specialization catalogs
portfolio/    Owner-protected project CRUD and media validation
briefs/       Private brand briefs, editable draft builder, Gemini adapter and quota
discovery/    Validated filters, deterministic scoring, usage warnings, comparison
templates/    Shared layouts, cards, forms, public and private views
static/       Committed CSS, vendor JS, original demo art
trust/        Private evidence uploads, reviewer permissions, revision-bound trust signals
engagements/  Invitation snapshots, status transitions, participant activity history
scripts/      Original art generator and Waitress production entry point
```

`User` has a CREATOR or BRAND role. A creator has one `CreatorProfile`; each profile has many `PortfolioItem` records. Profiles reference tools, skills, and specializations through M2M relations. Portfolio entries reference tools independently of profile claims. Availability and format are indexed; creator and portfolio lookups prefetch related records. Only a small read-only taxonomy API uses DRF (`GET /api/taxonomy/`).

`Brief` belongs to a brand user and references preferred tools, skills, and specializations. Database constraints enforce positive, ordered budget ranges. `GenerationUsage` stores quota counters, not prompts. Comparison is a bounded session list of up to three active public creators. Brief-specific scores and comparison always check the brand's ownership. `Engagement` links a brief to a creator, preserves the shared brief snapshot, and records role-authorized status changes in `EngagementEvent`. `Evidence` belongs to a portfolio project; review approval is bound to its incrementing revision number and becomes stale on edits.

## Discovery and matching

Directory filters combine with AND across skills, tools, specialization, availability, format, aspect ratio, and style. Tools can be listed on the profile or portfolio. Format, aspect ratio, and style must match the **same** portfolio entry. Invalid filters return clear errors, and pagination keeps active filters. Empty results calculate actual result counts after removing each active filter, then suggest up to three useful relaxations.

Matching is deterministic Python, not a Gemini ranking. Weights: content type 25, aspect ratio 10, style 15, tools 20, skills 15, specializations 10, availability 5. Optional criteria omitted from the brief are excluded from the denominator; the remaining score is normalized to 100. Tools listed on portfolio entries get full credit; profile-only tool claims get half credit. Style uses word overlap within entries of the requested content type. Skills and specializations remain self-reported, and portfolio metadata is not independently verified. Ties use creator name, then ID.

Budget fit, price quotes, artistic quality, legal clearance, and deadline commitments are not inferred. Availability is the creator's general self-reported status. Commercial review flags missing usage notes, restriction phrases, linked-video rights questions, and fictional demo work. It always asks for actual source/tool-term review and never labels a creator legally certified or commercially cleared. These conservative flags are not a legal determination.

Suggested demo: register a brand → use the local builder → complete a product brief with `1:1`, `Sculptural product`, Blender, Art direction, and Product campaigns → save → view matches → inspect the score breakdown → add creators → compare against the brief. For empty-state discovery, combine `Product campaign` and `9:16` against the current seed, then use the offered filter relaxations.

## Demo media and data

`python manage.py seed_demo` creates 14 fictional profiles and 28 entries, without overwriting existing accounts or creating duplicate records on rerun. Usernames `demo_creator_01`–`demo_creator_14` are reserved by the seed; if a name already exists, it is skipped rather than claimed. Taxonomy records are also created by the seed and can be managed in Django admin.

All 29 artwork files (including the landing-page hero) are original procedural images generated with Pillow, supplied under the project MIT license. They are labeled demo artwork and do not claim to prove any AI tool’s output or a real person’s abilities. To regenerate them: `python scripts/generate_art.py`. Seeded entries copy the committed images into ignored `media/` storage.

## Validation

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

Tests use an isolated temporary database and temporary upload directory. `requirements.lock.txt` records the verified dependency versions; use `pip install -r requirements.lock.txt` for an exact recreation. CI runs system checks, migration drift checks, and tests.

Image uploads: JPEG/PNG/WebP, 5 MB maximum, 25 megapixels maximum; inspect actual image bytes, reject unsafe extensions, and randomize storage names. Video links: HTTPS YouTube watch/share URLs or public Vimeo numeric links; embed URLs are reconstructed from validated IDs and load only after the viewer clicks. No server-side remote URL fetching. Availability, skills, tools, and licensing notes are explicitly self-declared.

See [PHASE3_REPORT.md](PHASE3_REPORT.md) for current results, [DEMO_GUIDE.md](DEMO_GUIDE.md) for the presentation and architecture, and [DEPLOYMENT.md](DEPLOYMENT.md) for hosting configuration. Phase 1 and 2 reports preserve their milestone results.

## Evidence and engagement

Creators attach private screenshots or HTTPS proof links via Your evidence. Staff reviewers need the `trust.change_evidence` permission. Public labels distinguish Self-declared, Evidence Attached, and Admin Reviewed for current project revisions; review covers specific submitted claims, not identity or commercial rights. Demo portfolios cannot earn Admin Reviewed status.

Brands invite creators from brief matches after marking the brief Ready to shortlist. Invitation requires explicit sharing consent. Creators accept or decline, start work, and submit an HTTPS delivery link; brands request revisions or complete the engagement. Engagements appear in both participants� workspaces. No email is sent. Briefs with engagement history must be archived rather than deleted.

Optional showcase data: register a brand, then run `python manage.py seed_showcase --brand YOUR_USERNAME`. This adds two labelled demo briefs without overwriting edits or sending invitations.

# CREO — Phase 2 delivery report

Completed locally on 13 October 2026. Phase 1 functionality is retained. Phase 3 has not been started.

## Implemented

### Brand workspace and briefs

- Brand dashboard with persisted brief counts, status, budget, deadline, and actions.
- Private brief CRUD: title, description, audience, deliverables, content type, visual style, aspect ratio, budget range/currency, deadline, commercial-use intent, usage requirements, and optional tool/skill/specialization requirements.
- Draft, ready-to-shortlist, and archived statuses. Deletion requires a confirmation page and CSRF-protected POST.
- Brand ownership enforced for detail, edit, delete, matching, and brief-specific comparison. Creator accounts cannot manage briefs.
- Server-side validation and database budget constraints; unchanged historic deadlines can be retained while archiving an old brief.

### Editable brief builder

- Gemini REST adapter requests structured JSON and independently validates its shape, allowed fields, strict types, lengths, enums, budgets, and dates.
- Explicit idea-sharing consent, server-only credentials, a model allowlist, free-tier configuration acknowledgement, request timeout, bounded response size, and safe error messages.
- No automatic retries, paid fallback, external tools, or additional service dependencies.
- Database-backed 30-second cooldown and ten-attempt daily limit per account.
- Drafts are kept in the owner's session, bounded to three recent drafts and separated by opaque IDs. They become database Brief records only after review and validated save.
- Clearly labeled local starter preserves the rough idea and supplies a template without claiming AI generation. This works without credentials or network access.

### Discovery, matching, and comparison

- Keyword plus skill, tool, specialization, format, style, aspect ratio, and availability filters. Portfolio format/style/aspect constraints must match one entry together.
- Filter-preserving pagination, HTMX result updates, invalid-filter feedback, and empty-state suggestions with real counts after relaxing individual requirements.
- Deterministic Python ranking with per-category points and explanations. Optional criteria are removed from the denominator; ties are stable.
- Format 25, aspect ratio 10, style 15, tools 20, skills 15, specialization 10, availability 5. Portfolio-listed tools receive full credit, profile-only claims half credit. Style uses text overlap, not image analysis.
- Commercial review notes flag missing usage information, restriction phrases, linked-video rights questions, and demo media. No legal clearance, quality certification, or guaranteed budget/deadline fit is asserted.
- Session-based comparison of up to three public creators with portfolios, tools, skills, specializations, availability, and optional owner-private brief scores. Inactive/deleted creators are removed from the selection.
- Reusable templates and responsive Phase 2 styles extend the existing dark design system.

## Verification

| Check | Result |
| --- | --- |
| New `briefs` migration | Applied successfully to local SQLite |
| Django system checks | Passed, zero issues |
| Migration drift check | Passed, no changes detected |
| Full automated suite | **68 tests passed**, including all 32 Phase 1 tests |
| Tailwind build | Passed |
| Static collection | Passed |
| Actual browser: brand registration | Passed with a disposable local QA account |
| Actual browser: local builder → edit → save | Passed; saved details and LOCAL provenance displayed |
| Matches and comparison | Verified through full Django request/response integration tests and database-backed scoring tests |
| Live Gemini generation | Not tested; free-tier configuration is absent |
| PostgreSQL / Replit deployment | Not tested; SQLite local fallback used |

New tests exercise brief persistence, roles and ownership, CSRF, source/owner injection, cross-brand draft isolation, budget/date/usage validation, local draft review, consent, missing configuration, quota/cooldown, mocked successful generation, malformed and blocked responses, timeout and HTTP failures, oversized responses, unknown models, matching arithmetic, profile-only half credit, missing portfolios, optional-weight normalization, style overlap, commercial warnings, repeatable ranking, bounded database queries, combined filters, same-entry constraints, invalid filters, preserved pagination, smart relaxations, comparison limits, deduplication, safe redirects, and inactive-profile pruning.

The final test run initially encountered Windows sandbox denial of the temporary upload directories. Rerunning the same suite with the required filesystem permission completed successfully: 68 tests in 17.941 seconds. System checks and static collection also completed successfully.

The user interruption closed the browser session after the saved-brief check. Browser security policy rejected reconnecting to the remaining tab. Further browser QA was not attempted through another route. Consequently, Phase 2 visual screenshots, mobile layout checks, and browser interaction with matches/comparison are not claimed as verified. Those endpoints and their rendered content pass integration tests.

The disposable QA account and its single test brief were removed. The original 14 demo creators and 28 portfolio entries remain intact. No real user account, portfolio, or environment secret was overwritten.

## Run and demonstrate

The local database is already migrated. From this workspace:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000, register a **Brand**, and open the workspace. Use the local builder or write a brief manually. A suitable example for the existing fictional catalog:

- Content type: Product campaign
- Style: Sculptural product
- Aspect ratio: 1:1
- Tool: Blender
- Skill: Art direction
- Specialization: Product campaigns
- Your chosen future deadline, budget, currency, and usage requirements

Save → Find creator matches → inspect score breakdown and commercial review notes → add up to three creators → compare against the brief.

For empty results, combine Product campaign and 9:16 in discovery, then try a suggested relaxation.

## Optional Gemini setup

Use an API key from a project kept on Google's free tier, without enabling paid billing. Configure:

```dotenv
GEMINI_API_KEY=your-server-side-key
GEMINI_FREE_TIER_CONFIRMED=True
GEMINI_MODEL=gemini-3.5-flash-lite
```

The flag acknowledges the operator's tier check; CREO cannot independently prove billing status. The implementation and allowlist follow Google's [structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en) and [pricing documentation](https://ai.google.dev/gemini-api/docs/pricing) checked on 13 October 2026. Verify current model availability and free-tier eligibility before enabling the integration. No live API request was made during this delivery.

## Remaining limitations

- Matching is metadata-based and does not evaluate imagery, prove tool proficiency, negotiate rates, or verify delivery capacity. Fictional demo work is labeled and explicitly excluded from real capability claims.
- Commercial review is conservative text screening, with possible false positives and missed restrictions. It never replaces review of actual licenses, model-plan terms, source assets, or releases.
- The local starter is a template, not semantic AI extraction. Budget, dates, formats, and other unknowns need review and completion.
- Comparisons are session-scoped, not permanent saved shortlists. Changing browsers or losing the session loses that selection.
- Ranking loads the public catalog for deterministic scoring; suitable for this prototype, not yet tuned for a very large marketplace.
- Production deployment, email/password-reset flows, general authentication rate limiting, persistent hosted media, and media cleanup retain the Phase 1 limitations.
- Invitations, engagement statuses, evidence-backed verification, comparative test shots, and Phase 3 delivery work remain deferred.

**Stopped after Phase 2. Phase 3 requires explicit user approval.**

<div align="center">

<img src="static/img/mark.svg" alt="CREO logo" width="84" />

CREO

Human Vision. New Possibilities.

The creative marketplace where great ideas find the right AI talent.

Discover creators. Understand their process. Build better briefs. Collaborate with confidence.

Launch CREO · Explore the Code · Deployment Guide

    

</div>

The idea

A stunning portfolio tells you what someone made. But does it tell you how they made it—or whether they're right for your project?

Brands need filmmakers, animators, motion designers, and generative artists who can deliver a particular creative vision. Yet discovering talent, assessing real capabilities, preparing briefs, and coordinating work often happen across disconnected tools.

CREO brings that journey into one place. It's a full-stack marketplace built around the creative process: creators showcase their work and workflow, while brands turn ideas into actionable briefs, find relevant people, and collaborate through delivery.

What CREO can do

<table>
<tr><th>For creators</th><th>For brands</th></tr>
<tr>
<td>

Build a profile with skills, specializations, tools, and availability.

Publish portfolio images and supported video links.

Explain each project's workflow, format, tools, and licensing notes.

Attach private evidence supporting specific claims.

Receive invitations, accept work, and submit deliverables.

</td>
<td>

Search and filter creators by relevant creative capabilities.

Create detailed briefs with deliverables, budget, deadlines, and usage needs.

Turn a rough idea into an editable draft with Google Gemini.

See explainable compatibility scores and compare up to three creators.

Invite talent, review deliveries, request revisions, and complete projects.

</td>
</tr>
</table>

The experience: from an idea to a collaborator

Imagine a fashion brand looking for an editor to color grade a 30-second cinematic campaign.

01 — Show the work. A creator uploads a color-grading project, adds their skills and tools, and describes the process behind the final result.

02 — Describe the vision. The brand enters a simple request: warm highlights, deep shadows, natural skin tones, and a premium cinematic finish.

03 — Build the brief. Gemini can propose a structured draft. The brand reviews and edits the details before saving; a manual/local starter is available without AI.

04 — Discover the talent. CREO ranks relevant creators, explains the compatibility signals, and lets the brand compare up to three profiles side by side.

05 — Make it happen. The brand invites a creator, who can accept, start work, and submit a delivery link. The brand can request changes or mark the project complete.

Important distinction: Gemini assists with brief drafting. Creator matching uses explainable, rule-based scoring, not AI-generated rankings. A match score is a decision aid, not a guarantee of quality.

Features at a glance

Feature

What it delivers

Creator profiles

Skills, specializations, AI tools, bio, availability, and creative identity

Process-rich portfolios

Images or supported video links, tools/models, formats, aspect ratios, workflows, and licensing notes

Discovery & filtering

Search and combined filters to narrow down relevant talent

Creative briefs

Audience, style, content type, deliverables, budget, deadlines, and commercial-use requirements

Gemini brief builder

Optional AI-assisted drafting with editable output and a non-AI fallback

Explainable matching

Compatibility rankings with reasons and relevant portfolio signals

Creator comparison

Side-by-side comparison of up to three creators

Evidence review

Private claim evidence and administrator review status

Collaboration workflow

Invitations, acceptance, delivery links, revision requests, and completion

Technology behind CREO

Layer

Technologies

Why they're used

Backend

Python, Django 5.2, Django REST Framework

Authentication, permissions, business logic, and data handling

Frontend

Django Templates, Tailwind CSS

Fast, responsive, server-rendered pages

Interactions

HTMX, Alpine.js

Lightweight dynamic updates without a separate SPA

Database

PostgreSQL on Neon

Persistent creator, portfolio, brief, and collaboration records

AI

Google Gemini REST API

Optional structured creative-brief generation

Matching

Python, Django ORM

Transparent, rule-based creator compatibility scoring

Deployment

Render, Waitress, WhiteNoise

Application serving and static asset delivery

Local development

SQLite

Easy setup without provisioning PostgreSQL

Architecture

flowchart LR
    C[Creator] --> UI[CREO Web App]
    B[Brand] --> UI
    UI --> DJ[Django Backend]
    DJ --> DB[(PostgreSQL / Neon)]
    DJ --> P[Profiles & Portfolios]
    DJ --> BR[Creative Briefs]
    DJ --> M[Search & Matching]
    DJ --> W[Evidence & Collaboration]
    BR -. Optional draft generation .-> AI[Google Gemini API]

Try the live demo

Open CREO →

Create a Creator account to build a profile and publish work, or a Brand account to write a brief and discover matching creators.

For a quick walkthrough:

Open Discover creators and inspect a creator's portfolio and creative workflow.

Sign in as a Brand, open My workspace, and choose Create a brief.

Select Try the brief builder, describe a project, and generate an editable draft using Gemini (when configured).

Save the brief and choose Find Creator Matches.

Expand Why this match, then add creators to Compare.

Explore invitations and the delivery/revision workflow.

The project includes a fictional showcase catalog of 14 demo creators and 28 demo portfolio projects. Demo profiles and procedural artwork are illustrative, not evidence of real client work or verified AI skills.

Run locally

Requirements: Python 3.11+ and Git. PostgreSQL is optional for local development.

1. Clone and install

git clone https://github.com/aahanasingh819-collab/CREO.git
cd CREO
python -m venv .venv

Activate the environment:

Windows (CMD)

.venv\Scripts\activate

macOS / Linux

source .venv/bin/activate

Then install dependencies:

python -m pip install -r requirements.txt

2. Configure the environment

Copy .env.example to .env and adjust values for your setup. For a quick local run, omit DATABASE_URL to use SQLite.

DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace-with-a-unique-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: PostgreSQL
# DATABASE_URL=postgresql://user:password@host:5432/database

# Optional: Gemini brief builder
GEMINI_API_KEY=
GEMINI_FREE_TIER_CONFIRMED=False
GEMINI_MODEL=gemini-3.5-flash-lite

Gemini access depends on the availability of your configured model and API quota. Do not commit real API keys. Set the free-tier confirmation only after verifying your account's configuration.

3. Prepare the database and start

python manage.py migrate
python manage.py seed_demo
python manage.py runserver

Open http://127.0.0.1:8000/.

The seeded demo accounts have unusable passwords. Register your own Creator or Brand account to test authenticated flows.

To create an administrator or run the test suite:

python manage.py createsuperuser
python manage.py check
python manage.py test

Deployment

The live demo runs on Render, backed by Neon PostgreSQL. Production settings include:

DJANGO_DEBUG=False and a strong DJANGO_SECRET_KEY

DJANGO_ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS for the public domain

DATABASE_URL for the production PostgreSQL database

DATABASE_MEDIA=True for database-backed uploads on an ephemeral filesystem

SEED_DEMO=True if the fictional showcase catalog should be provisioned

Optional GEMINI_API_KEY, GEMINI_FREE_TIER_CONFIRMED, and GEMINI_MODEL

The standard production start command is:

python scripts/render_start.py

It applies migrations, optionally seeds the demo catalog, and starts Waitress. See DEPLOYMENT.md for deployment details.

Repository guide

accounts/       Authentication, roles, and user accounts
creators/       Creator profiles, skills, tools, specializations
portfolio/      Projects, media references, and storage
briefs/         Brand briefs and Gemini-assisted drafting
discovery/      Search, matching, and creator comparison
trust/          Evidence submission and review
engagements/    Invitations, delivery, revisions, activity history
config/         Django settings and routing
templates/      Website pages
static/         Styles, scripts, and demo artwork
scripts/        Deployment startup and demo asset utilities

Trust, transparency & scope

CREO is a marketplace prototype. Creator tools and experience may be self-reported. Evidence review is limited to submitted claims; it does not certify identity, ownership, or commercial usage rights. AI-generated briefs must be reviewed by the brand before use. Matching scores explain available signals and should not be treated as endorsements.

License

See LICENSE for licensing and THIRD_PARTY_NOTICES.md for third-party notices.

<div align="center">

CREO — Human Vision. New Possibilities.

From the first idea to the final delivery.

Explore CREO

</div>

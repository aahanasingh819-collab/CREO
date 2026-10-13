# CREO deployment

The release uses Django + Waitress + WhiteNoise. No Node server, worker queue, or paid service is required. Deployment configurations are provided; no hosted deployment has been executed in this workspace.

## Prepare

1. Install Python 3.12 and `pip install -r requirements.lock.txt`.
2. Set environment variables using your host's secrets manager. Do not commit `.env`.
3. Set `DJANGO_DEBUG=False`, a unique random `DJANGO_SECRET_KEY`, exact `DJANGO_ALLOWED_HOSTS`, and HTTPS `CSRF_TRUSTED_ORIGINS`.
4. Set `DATABASE_URL` to your PostgreSQL database. SQLite is suitable for local demonstrations; production instances must not each use a separate SQLite file.
5. Provide persistent, writable `MEDIA_ROOT` and `PRIVATE_MEDIA_ROOT` directories. Back up both alongside the database. Never expose `PRIVATE_MEDIA_ROOT` through a public web server or bucket.

```sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy
python scripts/serve.py
```

`PORT` defaults to 3000. Put Waitress behind an HTTPS proxy. Set `TRUSTED_PROXY_IP` to that proxy's exact source IP; Waitress trusts only its `X-Forwarded-Proto` header and sets the request scheme. Do not use a wildcard on a publicly reachable server. For another WSGI host, `TRUST_PROXY_HTTPS=True` is available only if its proxy strips client-supplied forwarding headers. Keep `SECURE_SSL_REDIRECT=True` in hosted use.

`/health/` checks database connectivity without exposing credentials. Configure HTTPS health probes or the trusted proxy correctly so probes do not loop through redirects. Static files are served by WhiteNoise; public portfolio images are streamed only for visible database records. Evidence files require authenticated ownership or reviewer permission and are never under the public media route.

The deploy check intentionally warns about HSTS subdomains and preloading. `SECURE_HSTS_INCLUDE_SUBDOMAINS` defaults to false because this app cannot establish ownership or HTTPS readiness of other subdomains. Preloading remains disabled. Configure a real domain and assess these policies before tightening them.

## Docker

```sh
docker build -t creo .
docker run --env-file .env.production -p 3000:3000 -v creo-media:/app/media -v creo-evidence:/app/private_media creo
```

Create `.env.production` outside version control with the production variables above and a reachable PostgreSQL URL. The image runs as a non-root user. It migrates and collects static files at startup; for multiple replicas run migrations once as a release step instead. The example requires your HTTPS proxy, not direct public HTTP. Docker build/run and PostgreSQL CI have not been executed locally.

## Replit

The existing `.replit` development command runs Django on port 3000. Install the pinned Python dependencies, configure Secrets, migrate, then seed the catalog. For a hosted release use `python scripts/serve.py` with the production settings and persistent database/media storage above. Ephemeral filesystems are unsuitable for uploads. The included GitHub Actions workflow tests SQLite and PostgreSQL separately when pushed.

## Operations and limits

- Create an admin with `python manage.py createsuperuser`. A staff account also needs `trust.change_evidence` to access the review queue; grant it through Django admin. There is no direct evidence-edit admin screen that bypasses review checks.
- Invitations are in-app only. This release sends no email or external messages and has no payments, contracts, or live chat.
- Gemini is optional. Keep billing disabled and explicitly confirm free-tier configuration before enabling it. Local drafting works without credentials.
- Uploaded files are not automatically purged when a record is deleted. Orphan files are inaccessible through app routes; establish an audited retention/cleanup policy and backup policy before real usage.
- Before opening public registration at scale, add host-level abuse controls, login throttling, monitoring, and a recovery/email delivery policy. The release is a hackathon prototype.

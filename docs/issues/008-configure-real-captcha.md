# [Security] Configure real Cloudflare Turnstile CAPTCHA

Labels: `security`, `frontend`, `backend`, `devops`, `task`

OpenSpec change: `openspec/changes/0007-delivery-flow-consolidation`

Spec path: `openspec/changes/0007-delivery-flow-consolidation/specs/progresia-studio/spec.md`

## Outcome

Enable real CAPTCHA verification in production registration/login flows using Cloudflare Turnstile.

## Context

Production is currently deployed with `CAPTCHA_ENABLED=false` so the initial launch can work before real Cloudflare keys exist. The frontend integration uses the real Cloudflare Turnstile script when `VITE_CAPTCHA_SITE_KEY` is present; activation still requires production keys.

## Tasks

- [ ] Create Cloudflare Turnstile site for `progresia.alumnes-monlau.com`.
- [x] Replace the simulated frontend control with the real Cloudflare Turnstile widget.
- [x] Pass `VITE_CAPTCHA_SITE_KEY` through the web Docker build.
- [ ] Add production site key to `VITE_CAPTCHA_SITE_KEY`.
- [ ] Add production secret key to `CAPTCHA_SECRET_KEY`.
- [ ] Set `CAPTCHA_PROVIDER=turnstile`.
- [ ] Set `CAPTCHA_ENABLED=true`.
- [ ] Rebuild the web container so the public site key is embedded in the frontend.
- [ ] Restart API so backend uses the secret key.
- [ ] Verify register/login reject missing or invalid CAPTCHA tokens.
- [ ] Document the operational steps in deployment docs.

## Validation

- [ ] `docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build`
- [ ] `curl https://progresia.alumnes-monlau.com/api/health`
- [ ] Browser smoke test: registration shows Turnstile control.
- [ ] Browser smoke test: valid CAPTCHA allows registration.
- [ ] Browser smoke test: invalid/missing CAPTCHA is rejected by API.

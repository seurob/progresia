# Tasks

- [x] Add OpenSpec change.
- [x] Add CAPTCHA backend verifier.
- [x] Add email verification DTOs and endpoints.
- [x] Send hashed one-time verification codes.
- [x] Block login for pending accounts.
- [x] Add frontend verification screen.
- [x] Update env examples and docs.
- [x] Support production CAPTCHA widgets for Turnstile, hCaptcha and reCAPTCHA.
- [x] Add SMTP transport timeouts, TLS options and auth validation.
- [ ] Add Redis-backed rate limiting.
- [ ] Add production email provider adapter beyond SMTP.

## Validation

- [x] `npm run openspec:check`
- [x] `npm run lint`
- [ ] `npm run typecheck` (web passed; api source passed with `npx tsc --noEmit`; npm script is blocked by Prisma Windows DLL lock)
- [x] `npm run test`
- [ ] `npm run build` (web passed; api source passed with `npx nest build`; root npm script is blocked by Prisma Windows DLL lock)

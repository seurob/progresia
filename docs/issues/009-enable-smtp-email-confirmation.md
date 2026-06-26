# [Auth] Enable SMTP email confirmation

Labels: `backend`, `frontend`, `security`, `devops`, `task`

OpenSpec change: `openspec/changes/0007-delivery-flow-consolidation`

Spec path: `openspec/changes/0007-delivery-flow-consolidation/specs/progresia-studio/spec.md`

## Outcome

Add a real account email-confirmation flow using a production SMTP mailbox for `progresia.alumnes-monlau.com`.

## Context

The domain DNS has mail records prepared, but no ProgresIA mailbox exists yet. The current app registers active accounts immediately and has no real verification-code flow.

## Tasks

- [ ] Create mailbox such as `no-reply@progresia.alumnes-monlau.com`.
- [ ] Configure SMTP environment variables in `.env.production`.
- [ ] Add `emailVerifiedAt` to `User`.
- [ ] Add a verification-code persistence model with hashed code, expiration, attempts and consumed timestamp.
- [ ] Add mail service for SMTP sending.
- [ ] Change register flow to create unverified accounts and send a code.
- [ ] Add `POST /api/auth/verify-email`.
- [ ] Add `POST /api/auth/resend-verification`.
- [ ] Block login or privileged workspace actions until email is verified.
- [ ] Add frontend verification-code screen after registration.
- [ ] Add tests for register, verify, resend, expired code and wrong code attempts.

## Validation

- [ ] `npm run typecheck --workspace @progresia/api`
- [ ] `npm run test --workspace @progresia/api`
- [ ] `npm run typecheck --workspace @progresia/web`
- [ ] Production smoke test: registration sends an email.
- [ ] Production smoke test: valid code verifies account.
- [ ] Production smoke test: wrong/expired code is rejected.
- [ ] SPF/DKIM/DMARC pass for sent messages.

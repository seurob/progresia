# Design: Secure Registration Verification

## Flow

1. Register validates CAPTCHA when enabled.
2. User is created as `PENDING_VERIFICATION`.
3. A 6 digit code is generated, hashed and stored with expiration.
4. Previous unused codes are invalidated before a new code is created.
5. Email is sent through SMTP when configured.
6. Login rejects pending accounts.
7. Verification activates the account and invalidates the code.

## Local Development

CAPTCHA is disabled unless `CAPTCHA_ENABLED=true`. SMTP is disabled unless `SMTP_HOST` is configured. This keeps local development possible without committing secrets.

## Security Constraints

- Codes are never stored in plaintext.
- Login errors avoid leaking unnecessary account details except for the required pending verification guidance.
- Resend and verification attempts are rate-limited in memory for MVP.
- Production should replace in-memory rate limits with Redis-backed limits.

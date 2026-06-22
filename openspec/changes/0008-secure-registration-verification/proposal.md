# Change: Secure Registration Verification

## Why

User accounts must not become active immediately after registration. The authentication flow needs bot protection and proof that the user controls the email address used during registration.

## What Changes

- Add configurable CAPTCHA validation for register/login.
- Create pending users and send a one-time email verification code.
- Block login until the account is active.
- Add endpoints to verify email, resend a code and change a pending email.
- Add frontend verification screen and safe auth messages.

## Impact

- Uses the existing `EmailVerificationCode` and account status data model.
- Adds email/CAPTCHA environment variables.
- Changes register response from immediate session to pending verification.

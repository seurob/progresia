## ADDED Requirements

### Requirement: Email Verification Before Login

The platform SHALL create registered users in a pending verification state and prevent login until the email verification code has been validated.

#### Scenario: Register pending account

- **GIVEN** a new user submits valid registration details
- **WHEN** CAPTCHA validation succeeds
- **THEN** the API SHALL create the user as pending verification
- **AND** generate a hashed, expiring verification code
- **AND** send the code through the configured email provider.

#### Scenario: Reject pending login

- **GIVEN** a user has not verified their email
- **WHEN** they try to log in
- **THEN** the API SHALL reject the login with a safe verification-required message.

#### Scenario: Verify email code

- **GIVEN** a pending user has a valid unexpired code
- **WHEN** they submit the code
- **THEN** the API SHALL activate the account
- **AND** invalidate the used code.

### Requirement: Configurable Bot Protection

The platform SHALL validate CAPTCHA tokens on the backend when bot protection is enabled.

#### Scenario: CAPTCHA enabled

- **GIVEN** `CAPTCHA_ENABLED=true`
- **WHEN** register, login, resend or pending-email change is requested
- **THEN** the backend SHALL verify the token with the configured provider before continuing.

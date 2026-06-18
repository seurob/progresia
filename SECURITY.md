# Security Policy

## Supported Versions

ProgresIA Studio is in early MVP development. Security fixes target the `main` branch until versioned releases exist.

## Reporting a Vulnerability

Do not open public issues for secrets, authentication bypasses, data exposure or dependency exploits.

Report privately through GitHub Security Advisories when available, or contact the repository owner directly.

Include:

- affected component,
- reproduction steps,
- expected impact,
- suggested mitigation when known.

## Baseline Controls

- CodeQL for JavaScript, TypeScript and Python.
- Dependency Review on pull requests.
- Dependabot version and security updates.
- OpenSSF Scorecard uploaded as SARIF.
- OpenSpec-linked issues for implementation work.

## Accepted Risks

### multer DoS (GHSA-72gw-mp4g-v24j, GHSA-3p4h-7m6x-2hcm) — High/Medium

**Affected package:** `multer` (transitive via `@nestjs/platform-express`).

**Risk:** Denial of Service via deeply nested field names or incomplete cleanup of aborted uploads.

**Mitigation:** ProgresIA Studio does not expose any file-upload endpoints. No route accepts `multipart/form-data`. The DoS attack surface is therefore not reachable. Fixing this requires downgrading `@nestjs/core` to 7.5.5, which would be a breaking change to the entire API.

**Decision:** Accept risk. Revisit when `@nestjs/platform-express` ships a patched `multer` version or an upstream upgrade path becomes available without breaking changes.

# Design: Web Foundation

## Route Model

- `/login`: existing user authentication.
- `/register`: create an Owner account.
- `/`: authenticated dashboard.
- `/projects/new`: create a project inside the user's first workspace.
- `/projects/:projectId`: project detail, idea wizard and specification list.

## State

The app stores the JWT access token in `localStorage` under `progresia.accessToken`. React Query handles server state and invalidation after mutations.

## API Client

The frontend uses a single Axios client configured from `VITE_API_URL`. Requests automatically attach the bearer token when present.

## UI Principles

The first version is an operational application shell, not a marketing page. It prioritizes:

- Clear navigation.
- Dense but readable workspace/project state.
- Forms that match the current backend contracts.
- Visible error and loading states.

## Validation

Forms use Zod schemas before submitting requests. Server errors are displayed near the form.

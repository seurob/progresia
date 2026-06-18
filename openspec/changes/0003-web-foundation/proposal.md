# Change 0003: Web Foundation

## Summary

Implement the first usable frontend workflow for ProgresIA Studio.

## Motivation

The backend now supports authentication, workspaces, projects, idea intake and specification persistence. The web app must stop being a static landing screen and become the main operator surface for creating a project and capturing the idea that will feed the AI service.

## Scope

This change covers:

- Authenticated React application shell.
- Login and register screens.
- Token persistence in the browser.
- API client with bearer token injection.
- Dashboard with workspace and project overview.
- Project creation form.
- Project detail view.
- Idea wizard connected to the API.
- Specifications view connected to the API.

This change does not cover:

- Full assistant chat.
- Real-time job progress.
- Artifact ZIP download.
- GitHub integration.
- Fine-grained collaboration UI.

## Impact

- The product can be tested end to end from browser to API and database.
- Future AI service integration can use persisted project and idea records.
- Frontend routes become the primary place to continue product workflow implementation.

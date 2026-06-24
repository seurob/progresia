# Proposal: Generated Project Compliance

## Why

`Puntos_desarrollar.txt` identifies gaps between the generated project delivery flow and the product contract for README, multiplatform setup, docs, SDD, AI guidance, Docker, validation, GitHub readiness and educational value.

Without this change, the ZIP can be functionally downloadable while still missing the documentation and operational context needed for students and AI assistants to continue the project safely.

## What Changes

- Expand generated artifact manifests with product docs, development docs, API docs, AI docs, deployment docs, SDD plans, task tracking and infrastructure files.
- Render those files with project-aware content instead of generic stubs.
- Ensure ZIP export and GitHub publication include manifest-rendered files plus generated code.
- Add pre-download summary data to the frontend.
- Strengthen validation with README-stack coherence, documentation links and empty-directory checks.

## Non-Goals

- Full PDF export of specifications.
- Full implementation of every beginner/intermediate stack template.
- Production-grade RAG implementation for generated projects.

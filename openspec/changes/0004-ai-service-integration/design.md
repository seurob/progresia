# Design: AI Service Integration

## Flow

1. User saves idea intake in the web app.
2. User triggers "Generate OpenSpec with AI".
3. Web app calls `POST /api/specifications/project/:projectId/generate-openspec`.
4. API validates project access.
5. API loads project and idea.
6. API maps the records to the AI service schema.
7. API calls `POST /generate-openspec` on FastAPI.
8. API persists the returned spec as `Specification(type=OPENSPEC, status=GENERATED)`.
9. Web app refreshes the project detail.

## Configuration

The API uses `AI_SERVICE_URL`, defaulting to `http://127.0.0.1:8000`.

## Error Handling

- Missing project access returns existing project access errors.
- Missing idea returns `409 Conflict` because generation requires idea intake.
- AI service failures return `502 Bad Gateway`.

## Testing

Unit tests should cover successful generation and missing idea behavior with mocked Prisma/project access and mocked AI service client.

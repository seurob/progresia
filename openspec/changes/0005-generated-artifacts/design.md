# Design: Generated Artifact Bundles

## Scope

This change introduces the manifest boundary only. It does not yet generate source code files, write ZIP archives, or provision storage in MinIO.

## Runtime Flow

1. User saves an idea.
2. User generates OpenSpec through the AI service.
3. User asks the API to generate an artifact bundle.
4. The API selects the newest generated OpenSpec for the project.
5. The API persists a manifest with stable file entries and source metadata.

## Manifest Shape

The manifest is JSON and contains:

- `version`
- `project`
- `sourceSpecificationId`
- `generatedAt`
- `files[]`

Each file entry contains:

- `path`
- `kind`
- `description`
- `source`

## Future Extension

The manifest becomes the contract for actual file generation and ZIP export. Later changes can add storage keys, checksums, generation logs and download URLs without changing the user workflow.

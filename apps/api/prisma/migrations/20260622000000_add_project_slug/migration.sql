-- Add slug column: nullable first so existing rows can be backfilled
ALTER TABLE "Project" ADD COLUMN "slug" TEXT;

-- Backfill existing rows using their UUID as slug (temporary, harmless)
UPDATE "Project" SET "slug" = id WHERE "slug" IS NULL;

-- Enforce NOT NULL
ALTER TABLE "Project" ALTER COLUMN "slug" SET NOT NULL;

-- Add unique index
CREATE UNIQUE INDEX "Project_slug_key" ON "Project"("slug");

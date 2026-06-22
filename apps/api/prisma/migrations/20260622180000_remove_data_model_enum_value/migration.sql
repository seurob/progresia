-- RemoveEnumValue DATA_MODEL from SpecificationType
-- DATA_MODEL was a legacy placeholder used before the ISSUES type was introduced.
-- PostgreSQL does not support ALTER TYPE ... DROP VALUE, so the enum must be recreated.

-- Remove any stale rows that still carry the legacy value
DELETE FROM "Specification" WHERE "type" = 'DATA_MODEL';

-- Recreate the enum without DATA_MODEL
ALTER TYPE "SpecificationType" RENAME TO "SpecificationType_old";

CREATE TYPE "SpecificationType" AS ENUM (
  'REQUIREMENTS',
  'OPENSPEC',
  'ARCHITECTURE',
  'ISSUES',
  'TUTORIAL',
  'CODE',
  'TECH_PROPOSAL'
);

ALTER TABLE "Specification"
  ALTER COLUMN "type" TYPE "SpecificationType"
  USING "type"::text::"SpecificationType";

DROP TYPE "SpecificationType_old";

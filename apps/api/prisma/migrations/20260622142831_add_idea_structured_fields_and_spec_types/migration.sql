-- AlterEnum
-- This migration adds more than one value to an enum.
-- With PostgreSQL versions 11 and earlier, this is not possible
-- in a single migration. This can be worked around by creating
-- multiple migrations, each migration adding only one value to
-- the enum.


ALTER TYPE "SpecificationType" ADD VALUE 'CODE';
ALTER TYPE "SpecificationType" ADD VALUE 'TECH_PROPOSAL';

-- AlterTable
ALTER TABLE "Idea" ADD COLUMN     "aiNeeds" TEXT,
ADD COLUMN     "architectureStyle" TEXT,
ADD COLUMN     "dataNeeds" TEXT[],
ADD COLUMN     "deploymentTarget" TEXT,
ADD COLUMN     "expectedResults" TEXT[],
ADD COLUMN     "mainObjective" TEXT,
ADD COLUMN     "mandatoryTechs" TEXT,
ADD COLUMN     "techPreference" TEXT;

-- CreateEnum
CREATE TYPE "ArtifactBundleStatus" AS ENUM ('GENERATED', 'EXPORTED');

-- CreateTable
CREATE TABLE "ArtifactBundle" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "specificationId" TEXT NOT NULL,
    "status" "ArtifactBundleStatus" NOT NULL DEFAULT 'GENERATED',
    "manifest" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ArtifactBundle_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "ArtifactBundle" ADD CONSTRAINT "ArtifactBundle_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ArtifactBundle" ADD CONSTRAINT "ArtifactBundle_specificationId_fkey" FOREIGN KEY ("specificationId") REFERENCES "Specification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

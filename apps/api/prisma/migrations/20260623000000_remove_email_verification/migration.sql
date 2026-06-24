-- DropForeignKey
ALTER TABLE "EmailVerificationCode" DROP CONSTRAINT "EmailVerificationCode_userId_fkey";

-- DropIndex
DROP INDEX "EmailVerificationCode_userId_idx";

-- DropTable
DROP TABLE "EmailVerificationCode";

-- AlterTable
ALTER TABLE "User" DROP COLUMN "accountStatus",
DROP COLUMN "emailVerified",
DROP COLUMN "emailVerifiedAt";

-- DropEnum
DROP TYPE "AccountStatus";

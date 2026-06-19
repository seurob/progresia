-- Add REQUIREMENTS_READY to ProjectStatus enum (between DRAFT and SPEC_READY)
-- Clear bcrypt-hashed refresh tokens — incompatible with new SHA-256 scheme; users must re-login
ALTER TYPE "ProjectStatus" ADD VALUE 'REQUIREMENTS_READY' BEFORE 'SPEC_READY';
DELETE FROM "RefreshToken";

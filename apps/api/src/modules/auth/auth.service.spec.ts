import { ConflictException, UnauthorizedException } from "@nestjs/common";
import { JwtService } from "@nestjs/jwt";
import { ConfigService } from "@nestjs/config";
import { Role } from "@prisma/client";
import * as bcrypt from "bcryptjs";
import { AuthService } from "./auth.service";

const user = {
  id: "user-1",
  email: "owner@progresia.local",
  name: "Owner",
  passwordHash: bcrypt.hashSync("change_me_123", 4),
  role: Role.OWNER,
  createdAt: new Date("2026-01-01T00:00:00.000Z"),
  updatedAt: new Date("2026-01-01T00:00:00.000Z")
};
const captcha = { verify: jest.fn().mockResolvedValue(undefined) };

describe("AuthService", () => {
  const jwtService = {
    sign: jest.fn(() => "signed-token")
  } as unknown as JwtService;

  const configService = {
    get: jest.fn((key: string, def: string) => def)
  } as unknown as ConfigService;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("rejects duplicate registration", async () => {
    const prisma = {
      user: { findUnique: jest.fn().mockResolvedValue(user) }
    };
    const service = new AuthService(prisma as never, jwtService, configService, captcha as never);

    await expect(
      service.register({ name: "Owner", email: "owner@progresia.local", password: "change_me_123" })
    ).rejects.toBeInstanceOf(ConflictException);
  });

  it("registers an active user and returns auth tokens", async () => {
    const prisma = {
      user: { findUnique: jest.fn().mockResolvedValue(null) },
      workspace: { create: jest.fn().mockResolvedValue({}) },
      refreshToken: { create: jest.fn().mockResolvedValue({}) },
      $transaction: jest.fn().mockImplementation((input: unknown) => {
        const createdUser = { ...user };
        return (input as (tx: unknown) => unknown)({
          user: { create: jest.fn().mockResolvedValue(createdUser) },
          workspace: { create: jest.fn().mockResolvedValue({}) }
        });
      })
    };
    const service = new AuthService(prisma as never, jwtService, configService, captcha as never);

    const response = await service.register({ name: "Owner", email: "owner@progresia.local", password: "Change_me_123!" });

    expect(response).toHaveProperty("accessToken");
    expect(response).toHaveProperty("refreshToken");
    expect(response.user).toMatchObject({ id: "user-1", email: "owner@progresia.local" });
  });

  it("logs in and returns safe user data", async () => {
    const prisma = {
      user: { findUnique: jest.fn().mockResolvedValue(user) },
      refreshToken: { create: jest.fn().mockResolvedValue({}) }
    };
    const service = new AuthService(prisma as never, jwtService, configService, captcha as never);

    const response = await service.login({ email: "owner@progresia.local", password: "change_me_123" });

    expect(response.accessToken).toBe("signed-token");
    expect(response.refreshToken).toBeDefined();
    expect(response.user).toMatchObject({ id: "user-1", email: "owner@progresia.local", role: Role.OWNER });
    expect(response.user).not.toHaveProperty("passwordHash");
  });

  it("rejects invalid login credentials", async () => {
    const prisma = {
      user: { findUnique: jest.fn().mockResolvedValue(null) }
    };
    const service = new AuthService(prisma as never, jwtService, configService, captcha as never);

    await expect(
      service.login({ email: "missing@progresia.local", password: "change_me_123" })
    ).rejects.toBeInstanceOf(UnauthorizedException);
  });
});

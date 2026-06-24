import { HealthService } from "./health.service";
import { PrismaService } from "../../database/prisma.service";

describe("HealthService", () => {
  it("returns ok payload when DB is reachable", async () => {
    const prisma = { $queryRaw: jest.fn().mockResolvedValue([{ "?column?": 1 }]) } as unknown as PrismaService;
    const service = new HealthService(prisma);

    await expect(service.getHealth()).resolves.toMatchObject({
      status: "ok",
      service: "progresia-api",
      dependencies: { db: "ok" }
    });
  });

  it("returns degraded payload when DB is unreachable", async () => {
    const prisma = { $queryRaw: jest.fn().mockRejectedValue(new Error("connection refused")) } as unknown as PrismaService;
    const service = new HealthService(prisma);

    await expect(service.getHealth()).resolves.toMatchObject({
      status: "degraded",
      dependencies: { db: "error" }
    });
  });
});

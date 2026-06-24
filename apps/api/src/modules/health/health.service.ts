import { Injectable } from "@nestjs/common";
import { PrismaService } from "../../database/prisma.service";

@Injectable()
export class HealthService {
  constructor(private readonly prisma: PrismaService) {}

  async getHealth() {
    let dbStatus = "ok";
    try {
      await this.prisma.$queryRaw`SELECT 1`;
    } catch {
      dbStatus = "error";
    }

    return {
      status: dbStatus === "ok" ? "ok" : "degraded",
      service: "progresia-api",
      timestamp: new Date().toISOString(),
      dependencies: { db: dbStatus }
    };
  }
}

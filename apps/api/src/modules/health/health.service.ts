import { Injectable } from "@nestjs/common";

@Injectable()
export class HealthService {
  getHealth() {
    return {
      status: "ok",
      service: "progresia-api",
      timestamp: new Date().toISOString()
    };
  }
}

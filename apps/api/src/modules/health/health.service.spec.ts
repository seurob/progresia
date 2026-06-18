import { HealthService } from "./health.service";

describe("HealthService", () => {
  it("returns the API health payload", () => {
    const service = new HealthService();

    expect(service.getHealth()).toMatchObject({
      status: "ok",
      service: "progresia-api"
    });
  });
});

import { IdeasService } from "./ideas.service";

const USER_ID = "user-1";
const PROJECT_ID = "project-1";

describe("IdeasService", () => {
  it("persists the complete wizard intake", async () => {
    const prisma = {
      idea: {
        upsert: jest.fn().mockResolvedValue({ id: "idea-1", projectId: PROJECT_ID })
      }
    };
    const projectsService = {
      ensureProjectAccess: jest.fn().mockResolvedValue({ id: PROJECT_ID })
    };
    const service = new IdeasService(prisma as never, projectsService as never);

    await service.upsert(USER_ID, {
      projectId: PROJECT_ID,
      problem: "Manual project planning wastes time",
      targetUsers: "Small software teams",
      coreFeatures: ["Guided wizard", "Code generation"],
      complexity: "standard",
      needsAi: true,
      needsAuth: true,
      needsAdminPanel: false,
      mainObjective: "mvp",
      techPreference: "mandatory",
      mandatoryTechs: "React, NestJS, PostgreSQL",
      architectureStyle: "frontend_api",
      dataNeeds: ["relational", "cache"],
      aiNeeds: "local",
      deploymentTarget: "vps",
      expectedResults: ["zip", "github", "learning"]
    });

    expect(projectsService.ensureProjectAccess).toHaveBeenCalledWith(PROJECT_ID, USER_ID);
    expect(prisma.idea.upsert).toHaveBeenCalledWith({
      where: { projectId: PROJECT_ID },
      create: expect.objectContaining({
        projectId: PROJECT_ID,
        techPreference: "mandatory",
        mandatoryTechs: "React, NestJS, PostgreSQL",
        architectureStyle: "frontend_api",
        dataNeeds: ["relational", "cache"],
        aiNeeds: "local",
        deploymentTarget: "vps",
        expectedResults: ["zip", "github", "learning"]
      }),
      update: expect.objectContaining({
        techPreference: "mandatory",
        mandatoryTechs: "React, NestJS, PostgreSQL",
        architectureStyle: "frontend_api",
        dataNeeds: ["relational", "cache"],
        aiNeeds: "local",
        deploymentTarget: "vps",
        expectedResults: ["zip", "github", "learning"]
      })
    });
  });
});

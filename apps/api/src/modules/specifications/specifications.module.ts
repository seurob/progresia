import { Module } from "@nestjs/common";
import { AiServiceModule } from "../ai-service/ai-service.module";
import { ProjectsModule } from "../projects/projects.module";
import { SpecificationsController } from "./specifications.controller";
import { SpecificationExportService } from "./specifications.export.service";
import { SpecificationsService } from "./specifications.service";

@Module({
  imports: [ProjectsModule, AiServiceModule],
  controllers: [SpecificationsController],
  providers: [SpecificationsService, SpecificationExportService]
})
export class SpecificationsModule {}

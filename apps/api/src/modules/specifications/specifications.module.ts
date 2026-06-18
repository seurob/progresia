import { Module } from "@nestjs/common";
import { ProjectsModule } from "../projects/projects.module";
import { SpecificationsController } from "./specifications.controller";
import { SpecificationsService } from "./specifications.service";

@Module({
  imports: [ProjectsModule],
  controllers: [SpecificationsController],
  providers: [SpecificationsService]
})
export class SpecificationsModule {}

import { Module } from "@nestjs/common";
import { ProjectsModule } from "../projects/projects.module";
import { IdeasController } from "./ideas.controller";
import { IdeasService } from "./ideas.service";

@Module({
  imports: [ProjectsModule],
  controllers: [IdeasController],
  providers: [IdeasService]
})
export class IdeasModule {}

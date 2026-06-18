import { Module } from "@nestjs/common";
import { ProjectsModule } from "../projects/projects.module";
import { ArtifactsController } from "./artifacts.controller";
import { ArtifactsService } from "./artifacts.service";

@Module({
  imports: [ProjectsModule],
  controllers: [ArtifactsController],
  providers: [ArtifactsService]
})
export class ArtifactsModule {}

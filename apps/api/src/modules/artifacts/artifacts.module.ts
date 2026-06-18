import { Module } from "@nestjs/common";
import { AiServiceModule } from "../ai-service/ai-service.module";
import { GithubModule } from "../github/github.module";
import { ProjectsModule } from "../projects/projects.module";
import { StorageModule } from "../storage/storage.module";
import { ArtifactsController } from "./artifacts.controller";
import { ArtifactsService } from "./artifacts.service";

@Module({
  imports: [ProjectsModule, AiServiceModule, GithubModule, StorageModule],
  controllers: [ArtifactsController],
  providers: [ArtifactsService]
})
export class ArtifactsModule {}

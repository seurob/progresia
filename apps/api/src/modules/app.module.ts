import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { ConfigModule, ConfigService } from "@nestjs/config";
import { PrismaModule } from "../database/prisma.module";
import { AuthModule } from "./auth/auth.module";
import { HealthModule } from "./health/health.module";
import { AiServiceModule } from "./ai-service/ai-service.module";
import { ArtifactsModule } from "./artifacts/artifacts.module";
import { IdeasModule } from "./ideas/ideas.module";
import { JobsModule } from "./jobs/jobs.module";
import { StorageModule } from "./storage/storage.module";
import { ProjectsModule } from "./projects/projects.module";
import { SpecificationsModule } from "./specifications/specifications.module";
import { UsersModule } from "./users/users.module";
import { WorkspacesModule } from "./workspaces/workspaces.module";

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    BullModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get("REDIS_HOST", "localhost"),
          port: config.get<number>("REDIS_PORT", 6379)
        }
      })
    }),
    PrismaModule,
    HealthModule,
    AiServiceModule,
    AuthModule,
    UsersModule,
    WorkspacesModule,
    ProjectsModule,
    IdeasModule,
    SpecificationsModule,
    ArtifactsModule,
    JobsModule,
    StorageModule
  ]
})
export class AppModule {}

import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { IsBoolean, IsOptional, IsString, MinLength } from "class-validator";

export class PushToGithubDto {
  @ApiProperty({ description: "GitHub personal access token (not stored server-side)" })
  @IsString()
  @MinLength(1)
  githubToken!: string;

  @ApiProperty({ description: "New repository name (must not already exist under your account)" })
  @IsString()
  @MinLength(1)
  repoName!: string;

  @ApiPropertyOptional({ description: "Whether the new repo should be private", default: false })
  @IsBoolean()
  @IsOptional()
  isPrivate?: boolean;

  @ApiPropertyOptional({ description: "Repository description" })
  @IsString()
  @IsOptional()
  description?: string;
}

export interface PushToGithubResult {
  repoUrl: string;
  cloneUrl: string;
  commitSha: string;
}

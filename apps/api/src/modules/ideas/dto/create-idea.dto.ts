import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsArray,
  IsBoolean,
  IsOptional,
  IsString,
  MinLength
} from "class-validator";

export class CreateIdeaDto {
  @ApiProperty({ description: "UUID or slug of the project" })
  @IsString()
  @MinLength(1)
  projectId!: string;

  @ApiProperty({ example: "Las reservas de clases se gestionan manualmente." })
  @IsString()
  @MinLength(10)
  problem!: string;

  @ApiProperty({ example: "Academias pequenas y profesores particulares" })
  @IsString()
  @MinLength(2)
  targetUsers!: string;

  @ApiProperty({ example: ["CRUD de profesores", "Reserva de clases"] })
  @IsArray()
  @IsString({ each: true })
  coreFeatures!: string[];

  @ApiPropertyOptional({ example: "standard" })
  @IsOptional()
  @IsString()
  complexity?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsBoolean()
  needsAi?: boolean;

  @ApiPropertyOptional()
  @IsOptional()
  @IsBoolean()
  needsAuth?: boolean;

  @ApiPropertyOptional()
  @IsOptional()
  @IsBoolean()
  needsAdminPanel?: boolean;

  @ApiPropertyOptional({ example: "Debe ser desplegable con Docker." })
  @IsOptional()
  @IsString()
  constraints?: string;

  // Structured wizard fields (Sprint 0015)
  @ApiPropertyOptional({ example: "mvp" })
  @IsOptional()
  @IsString()
  mainObjective?: string;

  @ApiPropertyOptional({ example: "ai_recommends" })
  @IsOptional()
  @IsString()
  techPreference?: string;

  @ApiPropertyOptional({ example: "React + Laravel obligatorio" })
  @IsOptional()
  @IsString()
  mandatoryTechs?: string;

  @ApiPropertyOptional({ example: "frontend_api" })
  @IsOptional()
  @IsString()
  architectureStyle?: string;

  @ApiPropertyOptional({ example: ["relational", "cache"] })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  dataNeeds?: string[];

  @ApiPropertyOptional({ example: "online" })
  @IsOptional()
  @IsString()
  aiNeeds?: string;

  @ApiPropertyOptional({ example: "docker_local" })
  @IsOptional()
  @IsString()
  deploymentTarget?: string;

  @ApiPropertyOptional({ example: ["specs_pdf", "zip", "github"] })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  expectedResults?: string[];
}

import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsArray,
  IsBoolean,
  IsOptional,
  IsString,
  MaxLength,
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
  @MaxLength(2000)
  problem!: string;

  @ApiProperty({ example: "Academias pequenas y profesores particulares" })
  @IsString()
  @MinLength(2)
  @MaxLength(500)
  targetUsers!: string;

  @ApiProperty({ example: ["CRUD de profesores", "Reserva de clases"] })
  @IsArray()
  @IsString({ each: true })
  @MaxLength(200, { each: true })
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
  @MaxLength(1000)
  constraints?: string;

  @ApiPropertyOptional({ example: "mvp" })
  @IsOptional()
  @IsString()
  @MaxLength(100)
  mainObjective?: string;

  @ApiPropertyOptional({ example: "ai_recommends" })
  @IsOptional()
  @IsString()
  techPreference?: string;

  @ApiPropertyOptional({ example: "React + Laravel obligatorio" })
  @IsOptional()
  @IsString()
  @MaxLength(500)
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

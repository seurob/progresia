import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsArray,
  IsBoolean,
  IsOptional,
  IsString,
  IsUUID,
  MinLength
} from "class-validator";

export class CreateIdeaDto {
  @ApiProperty()
  @IsUUID()
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
}

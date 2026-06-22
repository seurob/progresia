import { ApiProperty } from "@nestjs/swagger";
import { SpecificationStatus, SpecificationType } from "@prisma/client";
import { IsEnum, IsObject, IsOptional, IsString, MinLength } from "class-validator";

export class CreateSpecificationDto {
  @ApiProperty({ description: "UUID or slug of the project" })
  @IsString()
  @MinLength(1)
  projectId!: string;

  @ApiProperty({ enum: SpecificationType })
  @IsEnum(SpecificationType)
  type!: SpecificationType;

  @ApiProperty({ enum: SpecificationStatus, required: false })
  @IsOptional()
  @IsEnum(SpecificationStatus)
  status?: SpecificationStatus;

  @ApiProperty({ example: { requirements: [] } })
  @IsObject()
  content!: Record<string, unknown>;
}

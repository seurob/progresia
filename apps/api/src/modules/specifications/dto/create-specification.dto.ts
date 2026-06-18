import { ApiProperty } from "@nestjs/swagger";
import { SpecificationStatus, SpecificationType } from "@prisma/client";
import { IsEnum, IsObject, IsOptional, IsUUID } from "class-validator";

export class CreateSpecificationDto {
  @ApiProperty()
  @IsUUID()
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

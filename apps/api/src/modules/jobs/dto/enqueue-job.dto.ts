import { ApiProperty } from "@nestjs/swagger";
import { IsString, IsUUID } from "class-validator";

export class EnqueueJobDto {
  @ApiProperty()
  @IsString()
  @IsUUID()
  projectId!: string;
}

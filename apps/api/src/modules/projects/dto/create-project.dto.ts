import { ApiProperty } from "@nestjs/swagger";
import { IsString, IsUUID, MinLength } from "class-validator";

export class CreateProjectDto {
  @ApiProperty()
  @IsUUID()
  workspaceId!: string;

  @ApiProperty({ example: "Reservas de clases particulares" })
  @IsString()
  @MinLength(2)
  name!: string;

  @ApiProperty({ example: "Educacion" })
  @IsString()
  @MinLength(2)
  sector!: string;

  @ApiProperty({ example: "SaaS operativo" })
  @IsString()
  @MinLength(2)
  productType!: string;

  @ApiProperty({ example: "Plataforma para gestionar profesores, alumnos, clases y reservas." })
  @IsString()
  @MinLength(10)
  description!: string;
}

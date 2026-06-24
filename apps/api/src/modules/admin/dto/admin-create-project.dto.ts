import { IsString } from "class-validator";

export class AdminCreateProjectDto {
  @IsString()
  name!: string;

  @IsString()
  sector!: string;

  @IsString()
  productType!: string;

  @IsString()
  description!: string;

  @IsString()
  ownerId!: string;
}

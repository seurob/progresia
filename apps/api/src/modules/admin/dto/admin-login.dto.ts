import { IsString, MinLength } from "class-validator";

export class AdminLoginDto {
  @IsString()
  identifier!: string;

  @IsString()
  @MinLength(1)
  password!: string;
}

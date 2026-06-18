import { ApiProperty } from "@nestjs/swagger";
import { IsEmail, IsString, MinLength } from "class-validator";

export class LoginDto {
  @ApiProperty({ example: "owner@progresia.local" })
  @IsEmail()
  email!: string;

  @ApiProperty({ minLength: 8, example: "change_me_123" })
  @IsString()
  @MinLength(8)
  password!: string;
}

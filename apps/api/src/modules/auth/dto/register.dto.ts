import { ApiProperty } from "@nestjs/swagger";
import { IsEmail, IsString, MinLength } from "class-validator";

export class RegisterDto {
  @ApiProperty({ example: "Ada Lovelace" })
  @IsString()
  @MinLength(2)
  name!: string;

  @ApiProperty({ example: "owner@progresia.local" })
  @IsEmail()
  email!: string;

  @ApiProperty({ minLength: 8, example: "change_me_123" })
  @IsString()
  @MinLength(8)
  password!: string;
}

import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { IsEmail, IsOptional, IsString, MinLength } from "class-validator";

export class ChangePendingEmailDto {
  @ApiProperty({ example: "wrong@progresia.local" })
  @IsEmail()
  currentEmail!: string;

  @ApiProperty({ example: "correct@progresia.local" })
  @IsEmail()
  newEmail!: string;

  @ApiProperty({ minLength: 8, example: "MyPass1!" })
  @IsString()
  @MinLength(8)
  password!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  captchaToken?: string;
}

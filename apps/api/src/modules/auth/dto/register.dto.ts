import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { IsEmail, IsOptional, IsString, Matches, MinLength } from "class-validator";

export class RegisterDto {
  @ApiProperty({ example: "Ada Lovelace" })
  @IsString()
  @MinLength(2)
  name!: string;

  @ApiProperty({ example: "owner@progresia.local" })
  @IsEmail()
  email!: string;

  @ApiProperty({
    minLength: 8,
    example: "MyPass1!",
    description: "Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número y 1 carácter especial"
  })
  @IsString()
  @MinLength(8, { message: "La contraseña debe tener al menos 8 caracteres" })
  @Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{};:,<.>?])/, {
    message: "La contraseña debe incluir al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%...)"
  })
  password!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  captchaToken?: string;
}

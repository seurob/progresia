import { Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as nodemailer from "nodemailer";

@Injectable()
export class EmailService {
  private readonly logger = new Logger(EmailService.name);

  constructor(private readonly config: ConfigService) {}

  async sendVerificationCode(to: string, name: string, code: string, expiresMinutes: number) {
    const host = this.config.get<string>("SMTP_HOST");

    if (!host) {
      this.logger.warn("SMTP_HOST is not configured; verification email was not sent.");
      return;
    }

    const transporter = nodemailer.createTransport({
      host,
      port: this.config.get<number>("SMTP_PORT", 587),
      secure: this.config.get<string>("SMTP_SECURE", "false") === "true",
      auth: this.config.get<string>("SMTP_USER")
        ? {
            user: this.config.get<string>("SMTP_USER"),
            pass: this.config.get<string>("SMTP_PASSWORD")
          }
        : undefined
    });

    await transporter.sendMail({
      from: this.config.get<string>("EMAIL_FROM", "ProgresIA Studio <no-reply@progresia.local>"),
      to,
      subject: "Verifica tu cuenta de ProgresIA Studio",
      text: [
        `Hola ${name},`,
        "",
        "Usa este codigo para verificar tu cuenta de ProgresIA Studio:",
        "",
        code,
        "",
        `Caduca en ${expiresMinutes} minutos. No compartas este codigo.`,
        "Si no has solicitado esta cuenta, ignora este mensaje."
      ].join("\n")
    });
  }
}

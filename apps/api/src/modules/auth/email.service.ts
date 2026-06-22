import { Injectable, Logger, ServiceUnavailableException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as nodemailer from "nodemailer";
import type { Transporter } from "nodemailer";

@Injectable()
export class EmailService {
  private readonly logger = new Logger(EmailService.name);
  private transporter?: Transporter;

  constructor(private readonly config: ConfigService) {}

  async sendVerificationCode(to: string, name: string, code: string, expiresMinutes: number) {
    const transporter = await this.getTransporter();

    if (!transporter) {
      this.logger.warn("SMTP_HOST is not configured; verification email was not sent.");
      return;
    }

    await transporter.sendMail({
      from: this.config.get<string>("EMAIL_FROM", "ProgresIA Studio <no-reply@progresia.local>"),
      replyTo: this.config.get<string>("EMAIL_REPLY_TO") || undefined,
      to,
      subject: "Verifica tu cuenta de ProgresIA Studio",
      text: this.renderText(name, code, expiresMinutes),
      html: this.renderHtml(name, code, expiresMinutes)
    });
  }

  private async getTransporter(): Promise<Transporter | undefined> {
    if (this.transporter) return this.transporter;

    const host = this.config.get<string>("SMTP_HOST");
    if (!host) return undefined;

    const user = this.config.get<string>("SMTP_USER");
    const pass = this.config.get<string>("SMTP_PASSWORD");
    const requireAuth = this.config.get<string>("SMTP_REQUIRE_AUTH", "false") === "true";

    if (requireAuth && (!user || !pass)) {
      throw new ServiceUnavailableException("SMTP authentication is required but not configured");
    }

    this.transporter = nodemailer.createTransport({
      host,
      port: this.config.get<number>("SMTP_PORT", 587),
      secure: this.config.get<string>("SMTP_SECURE", "false") === "true",
      connectionTimeout: this.config.get<number>("SMTP_CONNECTION_TIMEOUT_MS", 10_000),
      greetingTimeout: this.config.get<number>("SMTP_GREETING_TIMEOUT_MS", 10_000),
      socketTimeout: this.config.get<number>("SMTP_SOCKET_TIMEOUT_MS", 15_000),
      tls: {
        rejectUnauthorized: this.config.get<string>("SMTP_TLS_REJECT_UNAUTHORIZED", "true") !== "false"
      },
      auth: user
        ? {
            user,
            pass
          }
        : undefined
    });

    if (this.config.get<string>("SMTP_VERIFY_ON_SEND", "true") === "true") {
      await this.transporter.verify();
    }

    return this.transporter;
  }

  private renderText(name: string, code: string, expiresMinutes: number) {
    return [
      `Hola ${name},`,
      "",
      "Usa este codigo para verificar tu cuenta de ProgresIA Studio:",
      "",
      code,
      "",
      `Caduca en ${expiresMinutes} minutos. No compartas este codigo.`,
      "Si no has solicitado esta cuenta, ignora este mensaje."
    ].join("\n");
  }

  private renderHtml(name: string, code: string, expiresMinutes: number) {
    return [
      `<p>Hola ${this.escapeHtml(name)},</p>`,
      "<p>Usa este codigo para verificar tu cuenta de ProgresIA Studio:</p>",
      `<p style="font-size:24px;font-weight:700;letter-spacing:6px">${code}</p>`,
      `<p>Caduca en ${expiresMinutes} minutos. No compartas este codigo.</p>`,
      "<p>Si no has solicitado esta cuenta, ignora este mensaje.</p>"
    ].join("");
  }

  private escapeHtml(value: string) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
}

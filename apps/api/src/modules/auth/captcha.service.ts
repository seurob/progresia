import { BadRequestException, Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";

type CaptchaProvider = "turnstile" | "hcaptcha" | "recaptcha";

const VERIFY_URLS: Record<CaptchaProvider, string> = {
  turnstile: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
  hcaptcha: "https://hcaptcha.com/siteverify",
  recaptcha: "https://www.google.com/recaptcha/api/siteverify"
};

@Injectable()
export class CaptchaService {
  constructor(private readonly config: ConfigService) {}

  async verify(token: string | undefined, remoteIp?: string) {
    if (this.config.get<string>("CAPTCHA_ENABLED", "false") !== "true") {
      return;
    }

    if (!token) {
      throw new BadRequestException("Captcha verification is required");
    }

    const provider = this.config.get<CaptchaProvider>("CAPTCHA_PROVIDER", "turnstile");
    const secret = this.config.get<string>("CAPTCHA_SECRET_KEY");

    if (!secret) {
      throw new BadRequestException("Captcha is not configured");
    }

    const body = new URLSearchParams({ secret, response: token });
    if (remoteIp) body.set("remoteip", remoteIp);

    const response = await fetch(VERIFY_URLS[provider] ?? VERIFY_URLS.turnstile, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body
    });

    if (!response.ok) {
      throw new BadRequestException("Captcha verification failed");
    }

    const result = await response.json() as { success?: boolean };
    if (!result.success) {
      throw new BadRequestException("Captcha verification failed");
    }
  }
}

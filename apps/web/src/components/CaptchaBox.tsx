import { useEffect, useRef } from "react";

declare global {
  interface Window {
    turnstile?: {
      render: (element: HTMLElement, options: Record<string, unknown>) => string;
      remove: (id: string) => void;
    };
    hcaptcha?: {
      render: (element: HTMLElement, options: Record<string, unknown>) => string;
      remove: (id: string) => void;
    };
    grecaptcha?: {
      render: (element: HTMLElement, options: Record<string, unknown>) => string;
      reset: (id: string) => void;
    };
  }
}

type CaptchaProvider = "turnstile" | "hcaptcha" | "recaptcha";

const SCRIPT_URLS: Record<CaptchaProvider, string> = {
  turnstile: "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit",
  hcaptcha: "https://js.hcaptcha.com/1/api.js?render=explicit",
  recaptcha: "https://www.google.com/recaptcha/api.js?render=explicit"
};

export function CaptchaBox({ onToken }: { readonly onToken: (token: string) => void }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);
  const siteKey = import.meta.env.VITE_CAPTCHA_SITE_KEY as string | undefined;
  const provider = (import.meta.env.VITE_CAPTCHA_PROVIDER ?? "turnstile") as CaptchaProvider;

  useEffect(() => {
    if (!siteKey || !containerRef.current) return;
    const scriptUrl = SCRIPT_URLS[provider] ?? SCRIPT_URLS.turnstile;

    const render = () => {
      if (!containerRef.current || widgetIdRef.current) return;
      const api = getCaptchaApi(provider);
      if (!api) return;

      widgetIdRef.current = api.render(containerRef.current, {
        sitekey: siteKey,
        callback: (token: string) => onToken(token),
        "expired-callback": () => onToken("")
      });
    };

    if (!document.querySelector(`script[src="${scriptUrl}"]`)) {
      const script = document.createElement("script");
      script.src = scriptUrl;
      script.async = true;
      script.defer = true;
      script.onload = render;
      document.head.appendChild(script);
    } else {
      render();
    }

    return () => {
      const api = getCaptchaApi(provider);
      if (widgetIdRef.current && api) {
        api.remove(widgetIdRef.current);
      }
      widgetIdRef.current = null;
    };
  }, [onToken, provider, siteKey]);

  if (!siteKey) return null;

  return <div ref={containerRef} className="min-h-16" />;
}

function getCaptchaApi(provider: CaptchaProvider) {
  if (provider === "hcaptcha") return window.hcaptcha;
  if (provider === "recaptcha" && window.grecaptcha) {
    return {
      render: window.grecaptcha.render,
      remove: window.grecaptcha.reset
    };
  }
  return window.turnstile;
}

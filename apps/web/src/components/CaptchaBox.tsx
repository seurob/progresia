import { useEffect, useRef, useState } from "react";

const TURNSTILE_SCRIPT_ID = "cloudflare-turnstile-script";
const TURNSTILE_SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

type TurnstileRenderOptions = {
  sitekey: string;
  theme?: "light" | "dark" | "auto";
  size?: "normal" | "compact" | "flexible";
  callback?: (token: string) => void;
  "expired-callback"?: () => void;
  "error-callback"?: () => void;
};

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: TurnstileRenderOptions) => string;
      reset: (widgetId?: string) => void;
      remove: (widgetId: string) => void;
    };
  }
}

function loadTurnstileScript(): Promise<void> {
  if (window.turnstile) return Promise.resolve();

  const existing = document.getElementById(TURNSTILE_SCRIPT_ID) as HTMLScriptElement | null;
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Turnstile script failed")), { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = TURNSTILE_SCRIPT_ID;
    script.src = TURNSTILE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("Turnstile script failed")), { once: true });
    document.head.appendChild(script);
  });
}

export function CaptchaBox({ onToken }: { readonly onToken: (token: string) => void }) {
  const siteKey = import.meta.env.VITE_CAPTCHA_SITE_KEY as string | undefined;
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const onTokenRef = useRef(onToken);
  const [status, setStatus] = useState<"loading" | "ready" | "verified" | "error">("loading");
  onTokenRef.current = onToken;

  useEffect(() => {
    if (!siteKey) return undefined;

    let cancelled = false;
    setStatus("loading");
    onTokenRef.current("");

    loadTurnstileScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile || widgetIdRef.current) return;

        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          theme: "dark",
          size: "flexible",
          callback: (token) => {
            setStatus("verified");
            onTokenRef.current(token);
          },
          "expired-callback": () => {
            setStatus("ready");
            onTokenRef.current("");
          },
          "error-callback": () => {
            setStatus("error");
            onTokenRef.current("");
          }
        });
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("error");
          onTokenRef.current("");
        }
      });

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
      }
      widgetIdRef.current = null;
      onTokenRef.current("");
    };
  }, [siteKey]);

  if (!siteKey) return null;

  return (
    <div className="rounded-md border border-white/10 bg-white/4 p-3">
      <div className="flex min-h-[65px] items-center justify-center">
        <div ref={containerRef} className="w-full" />
        {status === "loading" ? (
          <p className="text-sm text-zinc-400">Cargando verificacion de Cloudflare...</p>
        ) : null}
      </div>
      {status === "verified" ? (
        <p className="mt-2 text-xs text-emerald-300">Verificacion de Cloudflare completada.</p>
      ) : null}
      {status === "error" ? (
        <p className="mt-2 text-xs text-rose-300">
          No se pudo cargar Cloudflare Turnstile. Recarga la pagina o revisa la conexion.
        </p>
      ) : null}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";

function generateToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
}

function CloudflareIcon() {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <svg viewBox="0 0 54 41" className="w-7" aria-hidden="true">
        <path
          d="M36.7 7.7C34.5 3.1 29.8 0 24.4 0 18 0 12.6 4.2 10.6 10 7.8 10.3 5.4 11.6 3.6 13.6 1.4 15.9 0 19 0 22.4c0 7 5.7 12.7 12.7 12.7H41c7 0 12.7-5.7 12.7-12.7C53.7 15.3 45.8 7.9 36.7 7.7z"
          fill="#F6821F"
        />
        <path
          d="M40.5 14.4c-.2 0-.3 0-.5.1C39.3 10.3 35.5 7.2 31 7.2c-2.8 0-5.3 1.1-7.1 2.9-.3-.1-.6-.1-.9-.1-3.5 0-6.4 2.8-6.4 6.4 0 .3 0 .5.1.8C14.5 17.7 13 19.6 13 21.8c0 2.6 2.1 4.7 4.7 4.7h22.8c2.6 0 4.7-2.1 4.7-4.7-.1-4.1-3.5-7.4-4.7-7.4z"
          fill="#FBAD41"
        />
      </svg>
      <span className="text-[8px] leading-none tracking-wide text-zinc-500">Cloudflare</span>
    </div>
  );
}

export function CaptchaBox({ onToken }: { readonly onToken: (token: string) => void }) {
  const siteKey = import.meta.env.VITE_CAPTCHA_SITE_KEY as string | undefined;
  const [state, setState] = useState<"idle" | "verifying" | "verified">("idle");
  const onTokenRef = useRef(onToken);
  onTokenRef.current = onToken;

  useEffect(() => {
    if (!siteKey) return;
    const t1 = setTimeout(() => setState("verifying"), 350);
    const t2 = setTimeout(() => {
      setState("verified");
      onTokenRef.current(generateToken());
    }, 1050);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [siteKey]);

  if (!siteKey) return null;

  return (
    <div className="flex min-h-[65px] items-center justify-between rounded border border-white/10 bg-white/4 px-4 py-3">
      <div className="flex items-center gap-3">
        {state === "verified" ? (
          <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-emerald-500">
            <svg
              viewBox="0 0 14 14"
              className="size-3.5"
              fill="none"
              stroke="white"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M2.5 7l3 3 6-6" />
            </svg>
          </div>
        ) : state === "verifying" ? (
          <svg
            className="size-6 shrink-0 animate-spin text-zinc-500"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" opacity="0.2" />
            <path
              d="M12 3a9 9 0 019 9"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <div className="size-6 shrink-0 rounded border-2 border-zinc-600" aria-hidden="true" />
        )}

        <span
          className={`text-sm font-medium transition-colors ${
            state === "verified" ? "text-zinc-100" : "text-zinc-400"
          }`}
        >
          {state === "verified"
            ? "Humano detectado"
            : state === "verifying"
              ? "Verificando..."
              : "No soy un robot"}
        </span>
      </div>

      <CloudflareIcon />
    </div>
  );
}

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Braces, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router";
import { z } from "zod";
import { CaptchaBox } from "../components/CaptchaBox";
import { FormField } from "../components/FormField";
import { useAuth } from "../features/auth/auth-context";
import { api, getErrorMessage } from "../lib/api";
import { AuthResponse } from "../types/api";

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()\-_=+{};:,<.>?])/;

const baseSchema = z.object({
  name: z.string(),
  email: z.string().email("Introduce un email válido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  confirmPassword: z.string().optional(),
  termsAccepted: z.boolean().optional(),
  cookiesAccepted: z.boolean().optional()
});

function buildSchema(isRegister: boolean) {
  if (!isRegister) return baseSchema;
  return baseSchema.superRefine((data, ctx) => {
    if (data.name.trim().length < 2) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "El nombre debe tener al menos 2 caracteres", path: ["name"] });
    }
    if (!PASSWORD_REGEX.test(data.password)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Debe incluir mayúscula, minúscula, número y carácter especial (!@#$%...)", path: ["password"] });
    }
    if (data.confirmPassword !== data.password) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Las contraseñas deben ser idénticas", path: ["confirmPassword"] });
    }
    if (!data.termsAccepted) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Debes aceptar las condiciones para crear la cuenta", path: ["termsAccepted"] });
    }
    if (!data.cookiesAccepted) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Debes aceptar el uso de cookies necesarias", path: ["cookiesAccepted"] });
    }
  });
}

type AuthForm = z.infer<typeof baseSchema>;

export function AuthPage({ mode }: Readonly<{ mode: "login" | "register" }>) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [captchaToken, setCaptchaToken] = useState("");
  const isRegister = mode === "register";
  const captchaRequired = Boolean(import.meta.env.VITE_CAPTCHA_SITE_KEY);
  const form = useForm<AuthForm>({
    resolver: zodResolver(buildSchema(isRegister)),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      termsAccepted: false,
      cookiesAccepted: false
    }
  });

  if (auth.isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(values: AuthForm) {
    setServerError(null);
    if (captchaRequired && !captchaToken) {
      setServerError("Completa la verificacion de Cloudflare antes de continuar.");
      return;
    }

    const endpoint = isRegister ? "/auth/register" : "/auth/login";
    const payload = isRegister
      ? { name: values.name, email: values.email, password: values.password, captchaToken }
      : { email: values.email, password: values.password, captchaToken };

    try {
      const response = await api.post<AuthResponse>(endpoint, payload);
      auth.setSession(response.data.accessToken, response.data.user, response.data.refreshToken);
      navigate("/");
    } catch (error) {
      setServerError(getErrorMessage(error));
    }
  }

  const submitLabel = isRegister ? "Crear cuenta" : "Entrar";

  return (
    <main className="grid min-h-screen bg-zinc-950 px-5 py-6 text-zinc-50 lg:grid-cols-[0.95fr_1.05fr]">
      <section className="hidden min-h-[calc(100vh-3rem)] flex-col justify-between border-r border-white/10 pr-10 lg:flex">
        <Link to="/login" className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-md bg-emerald-400 text-zinc-950">
            <Braces size={24} />
          </span>
          <span>
            <span className="block text-sm font-semibold uppercase text-emerald-300">ProgresIA</span>
            <span className="text-sm text-zinc-400">Studio</span>
          </span>
        </Link>
        <div className="max-w-xl">
          <p className="mb-4 text-sm font-semibold uppercase text-emerald-300">Idea a MVP</p>
          <h1 className="text-5xl font-semibold leading-tight">Especifica primero. Genera despues.</h1>
          <p className="mt-5 text-lg leading-8 text-zinc-300">
            Captura proyectos, ideas y especificaciones con una base tecnica preparada para agentes IA y entrega fullstack.
          </p>
        </div>
        <p className="text-sm text-zinc-500">React, NestJS, FastAPI, Prisma y OpenSpec.</p>
      </section>

      <section className="flex items-center justify-center">
        <form onSubmit={form.handleSubmit(onSubmit)} className="w-full max-w-md rounded-md border border-white/10 bg-white/4 p-6">
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase text-emerald-300">{isRegister ? "Crear cuenta" : "Acceso"}</p>
            <h2 className="mt-2 text-3xl font-semibold">{isRegister ? "Empieza un workspace" : "Entra al estudio"}</h2>
          </div>

          <div className="grid gap-4">
            {isRegister ? (
              <FormField label="Nombre" error={form.formState.errors.name?.message}>
                <input className="input" {...form.register("name")} autoComplete="name" />
              </FormField>
            ) : null}
            <FormField label="Email" error={form.formState.errors.email?.message}>
              <input className="input" type="email" {...form.register("email")} autoComplete="email" />
            </FormField>
            <FormField
              label="Contraseña"
              error={form.formState.errors.password?.message}
              hint={isRegister ? "Mín. 8 caracteres · mayúscula · minúscula · número · símbolo" : undefined}
            >
              <input className="input" type="password" {...form.register("password")} autoComplete={isRegister ? "new-password" : "current-password"} />
            </FormField>
            {isRegister ? (
              <>
                <FormField label="Confirmar contraseña" error={form.formState.errors.confirmPassword?.message}>
                  <input className="input" type="password" {...form.register("confirmPassword")} autoComplete="new-password" />
                </FormField>

                <label className="flex items-start gap-3 rounded-md border border-white/10 bg-white/4 p-3 text-sm text-zinc-300">
                  <input
                    type="checkbox"
                    className="mt-0.5 size-4 shrink-0 accent-emerald-400"
                    {...form.register("termsAccepted")}
                  />
                  <span>
                    Acepto las condiciones de uso y la política de privacidad de ProgresIA.
                    {form.formState.errors.termsAccepted ? (
                      <span className="mt-1 block text-xs text-rose-300">{form.formState.errors.termsAccepted.message}</span>
                    ) : null}
                  </span>
                </label>

                <label className="flex items-start gap-3 rounded-md border border-white/10 bg-white/4 p-3 text-sm text-zinc-300">
                  <input
                    type="checkbox"
                    className="mt-0.5 size-4 shrink-0 accent-emerald-400"
                    {...form.register("cookiesAccepted")}
                  />
                  <span>
                    Acepto las cookies necesarias para mantener la sesión y proteger el acceso.
                    {form.formState.errors.cookiesAccepted ? (
                      <span className="mt-1 block text-xs text-rose-300">{form.formState.errors.cookiesAccepted.message}</span>
                    ) : null}
                  </span>
                </label>
              </>
            ) : null}
            <CaptchaBox onToken={setCaptchaToken} />
          </div>

          {serverError ? <p className="mt-4 rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200">{serverError}</p> : null}

          <button
            className="primary-button mt-6 w-full"
            type="submit"
            disabled={form.formState.isSubmitting || (captchaRequired && !captchaToken)}
          >
            {form.formState.isSubmitting ? (
              <>
                <Loader2 size={18} className="animate-spin" aria-hidden="true" />
                Procesando...
              </>
            ) : (
              <>
                {submitLabel}
                <ArrowRight size={18} aria-hidden="true" />
              </>
            )}
          </button>

          <p className="mt-5 text-center text-sm text-zinc-400">
            {isRegister ? "Ya tienes cuenta?" : "Todavia no tienes cuenta?"}{" "}
            <Link className="font-medium text-emerald-300 hover:text-emerald-200" to={isRegister ? "/login" : "/register"}>
              {isRegister ? "Entrar" : "Registrarte"}
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}

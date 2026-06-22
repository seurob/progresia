import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, MailCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { CaptchaBox } from "../components/CaptchaBox";
import { FormField } from "../components/FormField";
import { api, getErrorMessage } from "../lib/api";

const verifySchema = z.object({
  email: z.string().email("Introduce un email valido"),
  code: z.string().length(6, "El codigo tiene 6 digitos")
});

const changeEmailSchema = z.object({
  currentEmail: z.string().email(),
  newEmail: z.string().email("Introduce el nuevo email"),
  password: z.string().min(8)
});

type VerifyForm = z.infer<typeof verifySchema>;
type ChangeEmailForm = z.infer<typeof changeEmailSchema>;

export function VerifyEmailPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const initialEmail = useMemo(() => new URLSearchParams(location.search).get("email") ?? "", [location.search]);
  const [message, setMessage] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [captchaToken, setCaptchaToken] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [showChangeEmail, setShowChangeEmail] = useState(false);

  const verifyForm = useForm<VerifyForm>({
    resolver: zodResolver(verifySchema),
    defaultValues: { email: initialEmail, code: "" }
  });
  const changeForm = useForm<ChangeEmailForm>({
    resolver: zodResolver(changeEmailSchema),
    defaultValues: { currentEmail: initialEmail, newEmail: "", password: "" }
  });

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  async function verify(values: VerifyForm) {
    setServerError(null);
    setMessage(null);
    try {
      await api.post("/auth/verify-email", values);
      setMessage("Cuenta verificada. Ya puedes iniciar sesion.");
      setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (error) {
      setServerError(getErrorMessage(error));
    }
  }

  async function resend() {
    const email = verifyForm.getValues("email");
    setServerError(null);
    setMessage(null);
    try {
      await api.post("/auth/resend-verification-code", { email, captchaToken });
      setCooldown(60);
      setMessage("Si la cuenta esta pendiente, enviaremos un nuevo codigo.");
    } catch (error) {
      setServerError(getErrorMessage(error));
    }
  }

  async function changeEmail(values: ChangeEmailForm) {
    setServerError(null);
    setMessage(null);
    try {
      const response = await api.post<{ email: string; message: string }>("/auth/change-pending-email", {
        ...values,
        captchaToken
      });
      verifyForm.setValue("email", response.data.email);
      changeForm.setValue("currentEmail", response.data.email);
      setShowChangeEmail(false);
      setCooldown(60);
      setMessage(response.data.message);
    } catch (error) {
      setServerError(getErrorMessage(error));
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-950 px-5 py-8 text-zinc-50">
      <section className="w-full max-w-md rounded-md border border-white/10 bg-white/[0.04] p-6">
        <div className="mb-6">
          <span className="grid size-11 place-items-center rounded-md bg-emerald-400 text-zinc-950">
            <MailCheck size={23} />
          </span>
          <p className="mt-4 text-sm font-semibold uppercase text-emerald-300">Verifica tu correo</p>
          <h1 className="mt-2 text-3xl font-semibold">Introduce el codigo recibido</h1>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            El codigo caduca pronto y solo se puede usar una vez. No lo compartas con nadie.
          </p>
        </div>

        <form className="grid gap-4" onSubmit={verifyForm.handleSubmit(verify)}>
          <FormField label="Email" error={verifyForm.formState.errors.email?.message}>
            <input className="input" type="email" {...verifyForm.register("email")} />
          </FormField>
          <FormField label="Codigo de 6 digitos" error={verifyForm.formState.errors.code?.message}>
            <input className="input tracking-[0.35em]" inputMode="numeric" maxLength={6} {...verifyForm.register("code")} />
          </FormField>

          {serverError ? <p className="rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-200">{serverError}</p> : null}
          {message ? <p className="rounded-md border border-emerald-400/30 bg-emerald-400/10 p-3 text-sm text-emerald-200">{message}</p> : null}

          <button className="primary-button w-full justify-center" disabled={verifyForm.formState.isSubmitting}>
            {verifyForm.formState.isSubmitting ? "Verificando" : "Verificar cuenta"}
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="mt-5 grid gap-3 border-t border-white/10 pt-5">
          <CaptchaBox onToken={setCaptchaToken} />
          <button className="secondary-button justify-center" onClick={resend} disabled={cooldown > 0}>
            {cooldown > 0 ? `Reenviar en ${cooldown}s` : "Reenviar codigo"}
          </button>
          <button className="subtle-link justify-center text-sm" onClick={() => setShowChangeEmail((value) => !value)}>
            Cambiar correo pendiente
          </button>
        </div>

        {showChangeEmail ? (
          <form className="mt-5 grid gap-3 rounded-md border border-white/10 p-4" onSubmit={changeForm.handleSubmit(changeEmail)}>
            <FormField label="Correo actual" error={changeForm.formState.errors.currentEmail?.message}>
              <input className="input" type="email" {...changeForm.register("currentEmail")} />
            </FormField>
            <FormField label="Nuevo correo" error={changeForm.formState.errors.newEmail?.message}>
              <input className="input" type="email" {...changeForm.register("newEmail")} />
            </FormField>
            <FormField label="Contraseña" error={changeForm.formState.errors.password?.message}>
              <input className="input" type="password" {...changeForm.register("password")} />
            </FormField>
            <button className="secondary-button justify-center" disabled={changeForm.formState.isSubmitting}>
              Actualizar correo
            </button>
          </form>
        ) : null}

        <p className="mt-5 text-center text-sm text-zinc-400">
          Ya verificaste tu cuenta? <Link className="text-emerald-300" to="/login">Iniciar sesion</Link>
        </p>
      </section>
    </main>
  );
}

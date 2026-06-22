import { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}

export function FormField({ label, error, hint, children }: Readonly<FormFieldProps>) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-medium text-zinc-200">{label}</span>
      {children}
      {hint && !error ? <span className="text-xs text-zinc-500">{hint}</span> : null}
      {error ? <span className="text-xs text-rose-300">{error}</span> : null}
    </label>
  );
}

import { AlertCircle, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { adminApi } from "./adminApi";

interface Props {
  onLogin: (token: string) => void;
}

export function AdminLoginForm({ onLogin }: Props) {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { accessToken } = await adminApi.login(identifier, password);
      onLogin(accessToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f3f4f6",
      fontFamily: "Inter, system-ui, -apple-system, sans-serif",
      padding: "1rem",
      color: "#111827",
    }}>
      <div style={{ width: "100%", maxWidth: "380px" }}>
        {/* Brand mark */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "56px",
            height: "56px",
            borderRadius: "14px",
            background: "linear-gradient(135deg, #1d4ed8, #2563eb)",
            boxShadow: "0 8px 20px rgba(37,99,235,0.28)",
            marginBottom: "1rem",
          }}>
            <ShieldCheck size={28} color="#fff" />
          </div>
          <h1 style={{ margin: "0 0 0.25rem", fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.01em" }}>
            Gestión Administrativa
          </h1>
          <p style={{ margin: 0, fontSize: "0.875rem", color: "#6b7280" }}>
            ProgresIA Studio · Acceso restringido
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: "#fff",
          borderRadius: "12px",
          boxShadow: "0 4px 6px rgba(0,0,0,0.04), 0 10px 30px rgba(0,0,0,0.08)",
          padding: "1.75rem",
        }}>
          <form onSubmit={(e) => void handleSubmit(e)}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 500, color: "#374151", marginBottom: "0.375rem" }}>
                Usuario o correo electrónico
              </label>
              <input
                type="text"
                className="adm-input"
                required
                autoFocus
                autoComplete="username"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="admin@progresia.local"
              />
            </div>

            <div style={{ marginBottom: error ? "1rem" : "1.25rem" }}>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 500, color: "#374151", marginBottom: "0.375rem" }}>
                Contraseña
              </label>
              <input
                type="password"
                className="adm-input"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.625rem 0.75rem",
                borderRadius: "6px",
                marginBottom: "1.25rem",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                fontSize: "0.875rem",
              }}>
                <AlertCircle size={15} style={{ flexShrink: 0 }} />
                {error}
              </div>
            )}

            <button
              type="submit"
              className="adm-btn adm-btn-primary"
              disabled={loading}
              style={{ width: "100%", justifyContent: "center", minHeight: "2.5rem" }}
            >
              {loading ? "Verificando..." : "Acceder al panel"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.75rem", color: "#9ca3af" }}>
          Solo administradores autorizados · No dejes la sesión abierta
        </p>
      </div>
    </div>
  );
}

import { X } from "lucide-react";
import { useEffect, useId, useState } from "react";
import { S } from "./adminStyles";
import type { AdminUser } from "./adminApi";

const ROLES = ["ADMIN", "OWNER", "COLLABORATOR", "REVIEWER"];
const ROLE_LABELS: Record<string, string> = {
  ADMIN: "Administrador",
  OWNER: "Propietario",
  COLLABORATOR: "Colaborador",
  REVIEWER: "Revisor",
};

interface Props {
  mode: "create" | "edit";
  user: AdminUser | null;
  onSave: (data: { name: string; email: string; password?: string; role: string }) => Promise<void>;
  onClose: () => void;
}

export function UserModal({ mode, user, onSave, onClose }: Readonly<Props>) {
  const uid = useId();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(user?.role ?? "OWNER");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setName(user?.name ?? "");
    setEmail(user?.email ?? "");
    setPassword("");
    setRole(user?.role ?? "OWNER");
    setError("");
  }, [user, mode]);

  async function handleSave() {
    setError("");
    setLoading(true);
    try {
      const data: { name: string; email: string; password?: string; role: string } = { name, email, role };
      if (password) data.password = password;
      await onSave(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  }

  const dialogStyle: React.CSSProperties = {
    position: "fixed",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    zIndex: 51,
    width: "calc(100% - 2rem)",
    maxWidth: "440px",
    maxHeight: "90vh",
    overflowY: "auto",
    border: "none",
    padding: 0,
    margin: 0,
    borderRadius: "10px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
    background: "#fff",
    display: "flex",
    flexDirection: "column",
  };

  return (
    <>
      {/* Backdrop — aria-hidden removes it from the accessibility tree */}
      <div
        aria-hidden="true"
        onClick={onClose}
        style={{
          position: "fixed", inset: 0,
          background: "rgba(0,0,0,0.45)",
          backdropFilter: "blur(2px)",
          zIndex: 50,
        }}
      />

      <dialog
        open
        style={dialogStyle}
        onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
        aria-labelledby={`${uid}-title`}
      >
        {/* Header */}
        <div style={S.modalHead}>
          <h3 id={`${uid}-title`} style={S.modalTitle}>
            {mode === "create" ? "Crear usuario" : "Editar usuario"}
          </h3>
          <button className="adm-close" onClick={onClose} aria-label="Cerrar">
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form
          onSubmit={(e) => { e.preventDefault(); void handleSave(); }}
          style={{ display: "flex", flexDirection: "column", flex: 1 }}
        >
          <div style={S.modalBody}>
            <div style={S.group}>
              <label style={S.label} htmlFor={`${uid}-name`}>Nombre</label>
              <input
                id={`${uid}-name`}
                type="text"
                required
                className="adm-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div style={S.group}>
              <label style={S.label} htmlFor={`${uid}-email`}>Correo electrónico</label>
              <input
                id={`${uid}-email`}
                type="email"
                required
                className="adm-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div style={S.group}>
              <label style={S.label} htmlFor={`${uid}-pw`}>
                Contraseña{" "}
                {mode === "edit" && (
                  <span style={{ fontWeight: 400, color: "#9ca3af", fontSize: "0.75rem" }}>
                    (vacío = sin cambios)
                  </span>
                )}
              </label>
              <input
                id={`${uid}-pw`}
                type="password"
                required={mode === "create"}
                className="adm-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: 0 }}>
              <label style={S.label} htmlFor={`${uid}-role`}>Rol</label>
              <select
                id={`${uid}-role`}
                className="adm-input"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
            </div>

            {error && (
              <p style={{ margin: "0.75rem 0 0", fontSize: "0.875rem", color: "#b91c1c" }} role="alert">
                {error}
              </p>
            )}
          </div>

          <div style={S.modalFoot}>
            <button type="button" className="adm-btn adm-btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="adm-btn adm-btn-primary" disabled={loading}>
              {loading ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </dialog>
    </>
  );
}

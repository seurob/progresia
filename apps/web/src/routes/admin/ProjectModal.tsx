import { X } from "lucide-react";
import { useEffect, useId, useState } from "react";
import { adminApi, type AdminProject, type AdminUser } from "./adminApi";
import { S } from "./adminStyles";

const STATUSES = ["DRAFT", "REQUIREMENTS_READY", "SPEC_READY", "GENERATING", "GENERATED", "REVIEW", "DEPLOYED"];
const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  REQUIREMENTS_READY: "Requisitos listos",
  SPEC_READY: "OpenSpec listo",
  GENERATING: "Generando...",
  GENERATED: "MVP generado",
  REVIEW: "En revisión",
  DEPLOYED: "Publicado",
};

interface SaveData {
  name: string;
  sector: string;
  productType: string;
  description: string;
  status: string;
  ownerId?: string;
}

interface Props {
  mode: "create" | "edit";
  project: AdminProject | null;
  token: string;
  onSave: (data: SaveData) => Promise<void>;
  onClose: () => void;
}

export function ProjectModal({ mode, project, token, onSave, onClose }: Readonly<Props>) {
  const uid = useId();
  const [name, setName] = useState(project?.name ?? "");
  const [description, setDescription] = useState(project?.description ?? "");
  const [sector, setSector] = useState(project?.sector ?? "");
  const [productType, setProductType] = useState(project?.productType ?? "");
  const [ownerId, setOwnerId] = useState(project?.workspace?.owner?.id ?? "");
  const [status, setStatus] = useState(project?.status ?? "DRAFT");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setName(project?.name ?? "");
    setDescription(project?.description ?? "");
    setSector(project?.sector ?? "");
    setProductType(project?.productType ?? "");
    setOwnerId(project?.workspace?.owner?.id ?? "");
    setStatus(project?.status ?? "DRAFT");
    setError("");
  }, [project, mode]);

  useEffect(() => {
    adminApi.getUsers(token).then(setUsers).catch(() => {});
  }, [token]);

  async function handleSave() {
    setError("");
    if (mode === "create" && !ownerId) {
      setError("Debes seleccionar un propietario");
      return;
    }
    setLoading(true);
    try {
      const data: SaveData = { name, sector, productType, description, status };
      if (mode === "create") data.ownerId = ownerId;
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
    maxWidth: "480px",
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
            {mode === "create" ? "Crear proyecto" : "Editar proyecto"}
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
              <label style={S.label} htmlFor={`${uid}-name`}>Nombre del proyecto</label>
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
              <label style={S.label} htmlFor={`${uid}-desc`}>Descripción</label>
              <textarea
                id={`${uid}-desc`}
                required
                rows={2}
                className="adm-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
              <div>
                <label style={S.label} htmlFor={`${uid}-sector`}>Sector</label>
                <input
                  id={`${uid}-sector`}
                  type="text"
                  required
                  className="adm-input"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                />
              </div>
              <div>
                <label style={S.label} htmlFor={`${uid}-type`}>Tipo de producto</label>
                <input
                  id={`${uid}-type`}
                  type="text"
                  required
                  className="adm-input"
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                />
              </div>
            </div>

            {mode === "create" && (
              <div style={S.group}>
                <label style={S.label} htmlFor={`${uid}-owner`}>Propietario</label>
                <select
                  id={`${uid}-owner`}
                  required
                  className="adm-input"
                  value={ownerId}
                  onChange={(e) => setOwnerId(e.target.value)}
                >
                  <option value="">Seleccionar propietario...</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>{u.name} ({u.email})</option>
                  ))}
                </select>
              </div>
            )}

            <div style={{ marginBottom: 0 }}>
              <label style={S.label} htmlFor={`${uid}-status`}>Estado</label>
              <select
                id={`${uid}-status`}
                className="adm-input"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
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

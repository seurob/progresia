import { CheckCircle2, FolderOpen, Pencil, Plus, Search, Trash2, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { adminApi, type AdminProject } from "./adminApi";
import { S } from "./adminStyles";
import { ProjectModal } from "./ProjectModal";

interface Props { token: string }

interface Toast { id: number; type: "success" | "error"; message: string }

interface SaveData {
  name: string;
  sector: string;
  productType: string;
  description: string;
  status: string;
  ownerId?: string;
}

let nextId = 0;

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  REQUIREMENTS_READY: "Requisitos",
  SPEC_READY: "OpenSpec",
  GENERATING: "Generando",
  GENERATED: "MVP listo",
  REVIEW: "Revisión",
  DEPLOYED: "Publicado",
};

export function ProjectsTab({ token }: Props) {
  const [projects, setProjects] = useState<AdminProject[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [modalMode, setModalMode] = useState<"create" | "edit" | null>(null);
  const [editingProject, setEditingProject] = useState<AdminProject | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function addToast(type: "success" | "error", message: string) {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.getProjects(token, search || undefined);
      setProjects(data);
    } catch {
      addToast("error", "Error al cargar proyectos");
    } finally {
      setLoading(false);
    }
  }, [token, search]);

  useEffect(() => { void load(); }, [load]);

  async function handleSave(data: SaveData) {
    if (modalMode === "create") {
      await adminApi.createProject(token, data as { name: string; sector: string; productType: string; description: string; ownerId: string });
      addToast("success", "Proyecto creado correctamente");
    } else if (editingProject) {
      await adminApi.updateProject(token, editingProject.id, data);
      addToast("success", "Proyecto actualizado correctamente");
    }
    setModalMode(null);
    setEditingProject(null);
    void load();
  }

  async function handleDelete(id: string) {
    try {
      await adminApi.deleteProject(token, id);
      addToast("success", "Proyecto eliminado");
      void load();
    } catch (err) {
      addToast("error", err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      setDeletingId(null);
    }
  }

  const deletingProject = projects.find((p) => p.id === deletingId);

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", gap: "0.75rem", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div className="adm-search">
            <span className="adm-search-icon"><Search size={14} /></span>
            <input
              type="search"
              className="adm-input"
              placeholder="Buscar por nombre..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ minWidth: "240px" }}
            />
          </div>
          {loading && <span style={{ fontSize: "0.8125rem", color: "#9ca3af" }}>Cargando...</span>}
        </div>
        <button
          className="adm-btn adm-btn-primary"
          onClick={() => { setEditingProject(null); setModalMode("create"); }}
        >
          <Plus size={15} />
          Nuevo proyecto
        </button>
      </div>

      {/* Table */}
      <div style={{ background: "#fff", borderRadius: "8px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
        {!loading && projects.length === 0 ? (
          <div style={{ padding: "3rem 2rem", textAlign: "center", color: "#9ca3af" }}>
            <FolderOpen size={32} style={{ margin: "0 auto 0.75rem", display: "block", color: "#d1d5db" }} />
            <p style={{ margin: 0, fontSize: "0.875rem" }}>
              {search ? `Sin resultados para "${search}"` : "No hay proyectos registrados"}
            </p>
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={S.th}>Proyecto</th>
                <th style={S.th}>Propietario</th>
                <th style={S.th}>Estado</th>
                <th style={S.th}>Creado</th>
                <th style={{ ...S.th, textAlign: "right" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id} className="adm-tr">
                  <td style={S.td}>
                    <div style={{ fontWeight: 500, color: "#111827" }}>{project.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "0.125rem" }}>
                      {project.sector} · {project.productType}
                    </div>
                  </td>
                  <td style={S.td}>
                    {project.workspace?.owner ? (
                      <div>
                        <div style={{ color: "#111827" }}>{project.workspace.owner.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>{project.workspace.owner.email}</div>
                      </div>
                    ) : (
                      <span style={{ color: "#9ca3af" }}>—</span>
                    )}
                  </td>
                  <td style={S.td}>
                    <span style={S.statusBadge(project.status)}>
                      {STATUS_LABELS[project.status] ?? project.status}
                    </span>
                  </td>
                  <td style={{ ...S.td, color: "#6b7280", fontSize: "0.8125rem" }}>
                    {new Date(project.createdAt).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" })}
                  </td>
                  <td style={{ ...S.td, textAlign: "right" }}>
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.25rem" }}>
                      <button
                        className="adm-action adm-action-edit"
                        onClick={() => { setEditingProject(project); setModalMode("edit"); }}
                      >
                        <Pencil size={13} />
                        Editar
                      </button>
                      <button
                        className="adm-action adm-action-del"
                        onClick={() => setDeletingId(project.id)}
                      >
                        <Trash2 size={13} />
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Delete confirmation */}
      {deletingId && (
        <div
          style={S.overlay}
          onClick={() => setDeletingId(null)}
          onKeyDown={(e) => { if (e.key === "Escape") setDeletingId(null); }}
          role="presentation"
        >
          <div
            role="dialog"
            aria-modal="true"
            style={S.modal("400px")}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
          >
            <div style={S.modalHead}>
              <h3 style={S.modalTitle}>Confirmar eliminación</h3>
              <button className="adm-close" onClick={() => setDeletingId(null)}>✕</button>
            </div>
            <div style={S.modalBody}>
              <p style={{ margin: 0, fontSize: "0.9375rem", color: "#374151" }}>
                ¿Eliminar el proyecto <strong>{deletingProject?.name ?? "este proyecto"}</strong>? Se perderán todas sus especificaciones e ideas.
              </p>
            </div>
            <div style={S.modalFoot}>
              <button className="adm-btn adm-btn-secondary" onClick={() => setDeletingId(null)}>
                Cancelar
              </button>
              <button
                className="adm-btn adm-btn-danger"
                onClick={() => void handleDelete(deletingId)}
              >
                Sí, eliminar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Project modal */}
      {modalMode && (
        <ProjectModal
          mode={modalMode}
          project={editingProject}
          token={token}
          onSave={handleSave}
          onClose={() => { setModalMode(null); setEditingProject(null); }}
        />
      )}

      {/* Toasts */}
      <div style={{ position: "fixed", top: "1rem", right: "1rem", zIndex: 100, display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "flex-end", pointerEvents: "none" }}>
        {toasts.map((t) => (
          <div key={t.id} style={S.toast(t.type)}>
            {t.type === "success" ? <CheckCircle2 size={15} style={{ flexShrink: 0 }} /> : <XCircle size={15} style={{ flexShrink: 0 }} />}
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}

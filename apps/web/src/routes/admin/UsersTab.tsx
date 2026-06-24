import { CheckCircle2, Pencil, Plus, Search, Trash2, UserX, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { adminApi, type AdminUser } from "./adminApi";
import { S } from "./adminStyles";
import { UserModal } from "./UserModal";

interface Props { token: string }

interface Toast { id: number; type: "success" | "error"; message: string }

let nextId = 0;

const ROLE_LABELS: Record<string, string> = {
  ADMIN: "Administrador",
  OWNER: "Propietario",
  COLLABORATOR: "Colaborador",
  REVIEWER: "Revisor",
};

export function UsersTab({ token }: Props) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [modalMode, setModalMode] = useState<"create" | "edit" | null>(null);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function addToast(type: "success" | "error", message: string) {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.getUsers(token, search || undefined);
      setUsers(data);
    } catch {
      addToast("error", "Error al cargar usuarios");
    } finally {
      setLoading(false);
    }
  }, [token, search]);

  useEffect(() => { void load(); }, [load]);

  async function handleSave(data: { name: string; email: string; password?: string; role: string }) {
    if (modalMode === "create") {
      await adminApi.createUser(token, data as { name: string; email: string; password: string; role: string });
      addToast("success", "Usuario creado correctamente");
    } else if (editingUser) {
      await adminApi.updateUser(token, editingUser.id, data);
      addToast("success", "Usuario actualizado correctamente");
    }
    setModalMode(null);
    setEditingUser(null);
    void load();
  }

  async function handleDelete(id: string) {
    try {
      await adminApi.deleteUser(token, id);
      addToast("success", "Usuario eliminado");
      void load();
    } catch (err) {
      addToast("error", err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      setDeletingId(null);
    }
  }

  const deletingUser = users.find((u) => u.id === deletingId);

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
              placeholder="Buscar por nombre o correo..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ minWidth: "240px" }}
            />
          </div>
          {loading && <span style={{ fontSize: "0.8125rem", color: "#9ca3af" }}>Cargando...</span>}
        </div>
        <button
          className="adm-btn adm-btn-primary"
          onClick={() => { setEditingUser(null); setModalMode("create"); }}
        >
          <Plus size={15} />
          Nuevo usuario
        </button>
      </div>

      {/* Table */}
      <div style={{ background: "#fff", borderRadius: "8px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
        {!loading && users.length === 0 ? (
          <div style={{ padding: "3rem 2rem", textAlign: "center", color: "#9ca3af" }}>
            <UserX size={32} style={{ margin: "0 auto 0.75rem", display: "block", color: "#d1d5db" }} />
            <p style={{ margin: 0, fontSize: "0.875rem" }}>
              {search ? `Sin resultados para "${search}"` : "No hay usuarios registrados"}
            </p>
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={S.th}>Nombre</th>
                <th style={S.th}>Email</th>
                <th style={S.th}>Rol</th>
                <th style={S.th}>Registrado</th>
                <th style={{ ...S.th, textAlign: "right" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="adm-tr">
                  <td style={{ ...S.td, fontWeight: 500, color: "#111827" }}>{user.name}</td>
                  <td style={{ ...S.td, color: "#6b7280" }}>{user.email}</td>
                  <td style={S.td}>
                    <span style={S.roleBadge(user.role)}>{ROLE_LABELS[user.role] ?? user.role}</span>
                  </td>
                  <td style={{ ...S.td, color: "#6b7280", fontSize: "0.8125rem" }}>
                    {new Date(user.createdAt).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" })}
                  </td>
                  <td style={{ ...S.td, textAlign: "right" }}>
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.25rem" }}>
                      <button
                        className="adm-action adm-action-edit"
                        onClick={() => { setEditingUser(user); setModalMode("edit"); }}
                      >
                        <Pencil size={13} />
                        Editar
                      </button>
                      <button
                        className="adm-action adm-action-del"
                        onClick={() => setDeletingId(user.id)}
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
            style={S.modal("380px")}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
          >
            <div style={S.modalHead}>
              <h3 style={S.modalTitle}>Confirmar eliminación</h3>
              <button className="adm-close" onClick={() => setDeletingId(null)}>✕</button>
            </div>
            <div style={S.modalBody}>
              <p style={{ margin: 0, fontSize: "0.9375rem", color: "#374151" }}>
                ¿Eliminar a <strong>{deletingUser?.name ?? "este usuario"}</strong>? Esta acción no se puede deshacer.
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

      {/* User modal */}
      {modalMode && (
        <UserModal
          mode={modalMode}
          user={editingUser}
          onSave={handleSave}
          onClose={() => { setModalMode(null); setEditingUser(null); }}
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

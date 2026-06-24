import { FolderOpen, LogOut, Users } from "lucide-react";
import { useState } from "react";
import { ProjectsTab } from "./ProjectsTab";
import { UsersTab } from "./UsersTab";

type Tab = "users" | "projects";

interface Props {
  token: string;
  onLogout: () => void;
}

export function AdminDashboard({ token, onLogout }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("users");

  return (
    <div className="adm">
      {/* Header */}
      <header style={{
        background: "#fff",
        borderBottom: "1px solid #e5e7eb",
        padding: "0 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "56px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
          <div style={{
            width: "28px",
            height: "28px",
            borderRadius: "7px",
            background: "#2563eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}>
            <span style={{ color: "#fff", fontSize: "0.8125rem", fontWeight: 700, letterSpacing: "-0.01em" }}>P</span>
          </div>
          <span style={{ fontSize: "0.9375rem", fontWeight: 700, color: "#111827" }}>ProgresIA</span>
          <span style={{ fontSize: "0.8125rem", color: "#9ca3af" }}>/ Admin</span>
        </div>

        <button className="adm-btn adm-btn-ghost" onClick={onLogout}>
          <LogOut size={14} />
          Cerrar sesión
        </button>
      </header>

      {/* Tabs */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e5e7eb", padding: "0 1.5rem" }}>
        <nav style={{ display: "flex" }}>
          <button
            className={`adm-tab${activeTab === "users" ? " active" : ""}`}
            onClick={() => setActiveTab("users")}
          >
            <Users size={14} />
            Usuarios
          </button>
          <button
            className={`adm-tab${activeTab === "projects" ? " active" : ""}`}
            onClick={() => setActiveTab("projects")}
          >
            <FolderOpen size={14} />
            Proyectos
          </button>
        </nav>
      </div>

      {/* Content */}
      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "1.5rem" }}>
        {activeTab === "users" ? <UsersTab token={token} /> : <ProjectsTab token={token} />}
      </main>
    </div>
  );
}

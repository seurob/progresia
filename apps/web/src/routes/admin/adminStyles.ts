import type { CSSProperties } from "react";

// Injected globally by AdminPage — CSS class selectors for hover/focus states
// without conflicting with the main app's Tailwind dark-theme overrides.
export const ADMIN_CSS = `
.adm { font-family: Inter, system-ui, -apple-system, sans-serif; color: #111827; background: #f3f4f6; min-height: 100vh; }
.adm *, .adm *::before, .adm *::after { box-sizing: border-box; }

.adm-input {
  display: block; width: 100%; font-family: inherit; font-size: 0.875rem;
  color: #111827; background: #fff; border: 1px solid #d1d5db; border-radius: 6px;
  padding: 0.5rem 0.75rem; outline: none; line-height: 1.5;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.adm-input:hover:not(:focus) { border-color: #9ca3af; }
.adm-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
.adm-input::placeholder { color: #9ca3af; }
textarea.adm-input { resize: vertical; min-height: 4rem; }
select.adm-input { cursor: pointer; }

.adm-btn {
  display: inline-flex; align-items: center; gap: 0.375rem; border-radius: 6px;
  padding: 0.5rem 1rem; font-size: 0.875rem; font-family: inherit; font-weight: 500;
  cursor: pointer; border: 1px solid; white-space: nowrap;
  transition: background 0.12s, border-color 0.12s, opacity 0.12s; line-height: 1.4;
}
.adm-btn:focus-visible { outline: 2px solid #3b82f6; outline-offset: 2px; }
.adm-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.adm-btn-primary   { background: #2563eb; border-color: #2563eb; color: #fff; }
.adm-btn-primary:hover:not(:disabled)   { background: #1d4ed8; border-color: #1d4ed8; }
.adm-btn-secondary { background: #fff; border-color: #d1d5db; color: #374151; font-weight: 400; }
.adm-btn-secondary:hover { background: #f9fafb; border-color: #9ca3af; }
.adm-btn-danger    { background: #dc2626; border-color: #dc2626; color: #fff; }
.adm-btn-danger:hover:not(:disabled)    { background: #b91c1c; border-color: #b91c1c; }
.adm-btn-ghost { background: none; border-color: transparent; color: #6b7280; padding: 0.375rem 0.5rem; font-size: 0.8125rem; font-weight: 400; }
.adm-btn-ghost:hover { background: #f3f4f6; color: #111827; }

.adm-tr { transition: background 0.06s; }
.adm-tr:hover > td { background: #f9fafb; }

.adm-action { background: none; border: none; cursor: pointer; font-family: inherit; font-size: 0.8125rem; font-weight: 500; padding: 0.2rem 0.4rem; border-radius: 4px; display: inline-flex; align-items: center; gap: 0.25rem; transition: background 0.1s; color: inherit; }
.adm-action-edit { color: #2563eb; }
.adm-action-edit:hover { background: #eff6ff; }
.adm-action-del  { color: #dc2626; }
.adm-action-del:hover  { background: #fef2f2; }

.adm-tab { background: none; border: none; border-bottom: 2px solid transparent; padding: 0.75rem 1rem; font-size: 0.875rem; font-family: inherit; cursor: pointer; margin-bottom: -1px; color: #6b7280; font-weight: 400; display: inline-flex; align-items: center; gap: 0.4rem; transition: color 0.1s, border-color 0.1s; }
.adm-tab:hover { color: #374151; }
.adm-tab.active { color: #2563eb; font-weight: 600; border-bottom-color: #2563eb; }

.adm-close { background: none; border: none; color: #9ca3af; cursor: pointer; padding: 0.3rem; border-radius: 4px; line-height: 0; transition: color 0.1s, background 0.1s; }
.adm-close:hover { color: #374151; background: #f3f4f6; }

.adm-search { position: relative; display: inline-flex; align-items: center; }
.adm-search-icon { position: absolute; left: 0.625rem; color: #9ca3af; pointer-events: none; display: flex; }
.adm-search .adm-input { padding-left: 2.125rem; }
`;

export const S = {
  overlay: {
    position: "fixed" as const,
    inset: 0,
    background: "rgba(0,0,0,0.45)",
    backdropFilter: "blur(2px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 50,
    padding: "1rem",
  } satisfies CSSProperties,

  modal(maxWidth = "440px"): CSSProperties {
    return {
      background: "#fff",
      borderRadius: "10px",
      boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
      width: "100%",
      maxWidth,
      maxHeight: "90vh",
      overflowY: "auto",
      display: "flex",
      flexDirection: "column",
    };
  },

  modalHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "1.25rem 1.5rem",
    borderBottom: "1px solid #f3f4f6",
    flexShrink: 0,
  } satisfies CSSProperties,

  modalTitle: {
    margin: 0,
    fontSize: "1rem",
    fontWeight: 600,
    color: "#111827",
  } satisfies CSSProperties,

  modalBody: {
    padding: "1.25rem 1.5rem",
    flex: 1,
  } satisfies CSSProperties,

  modalFoot: {
    display: "flex",
    gap: "0.75rem",
    justifyContent: "flex-end",
    padding: "1rem 1.5rem",
    borderTop: "1px solid #f3f4f6",
    background: "#fafafa",
    borderRadius: "0 0 10px 10px",
    flexShrink: 0,
  } satisfies CSSProperties,

  th: {
    padding: "0.625rem 1rem",
    textAlign: "left" as const,
    fontSize: "0.6875rem",
    fontWeight: 600,
    color: "#6b7280",
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    background: "#f9fafb",
    borderBottom: "1px solid #e5e7eb",
    whiteSpace: "nowrap" as const,
  } satisfies CSSProperties,

  td: {
    padding: "0.75rem 1rem",
    fontSize: "0.875rem",
    color: "#374151",
    borderBottom: "1px solid #f3f4f6",
    verticalAlign: "middle" as const,
  } satisfies CSSProperties,

  label: {
    display: "block",
    fontSize: "0.8125rem",
    fontWeight: 500 as const,
    color: "#374151",
    marginBottom: "0.3rem",
  } satisfies CSSProperties,

  group: { marginBottom: "1rem" } satisfies CSSProperties,

  toast(type: "success" | "error"): CSSProperties {
    return {
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      padding: "0.75rem 1rem",
      borderRadius: "6px",
      fontSize: "0.875rem",
      boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
      background: type === "success" ? "#f0fdf4" : "#fef2f2",
      color: type === "success" ? "#15803d" : "#b91c1c",
      border: `1px solid ${type === "success" ? "#bbf7d0" : "#fecaca"}`,
      minWidth: "220px",
      maxWidth: "340px",
    };
  },

  roleBadge(role: string): CSSProperties {
    const map: Record<string, { bg: string; color: string; border: string }> = {
      ADMIN:        { bg: "#ede9fe", color: "#5b21b6", border: "#c4b5fd" },
      OWNER:        { bg: "#e0f2fe", color: "#0369a1", border: "#7dd3fc" },
      COLLABORATOR: { bg: "#f3f4f6", color: "#374151", border: "#d1d5db" },
      REVIEWER:     { bg: "#f3f4f6", color: "#374151", border: "#d1d5db" },
    };
    const c = map[role] ?? map["COLLABORATOR"]!;
    return {
      display: "inline-block",
      padding: "0.175rem 0.55rem",
      borderRadius: "4px",
      fontSize: "0.6875rem",
      fontWeight: 600,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      background: c.bg,
      color: c.color,
      border: `1px solid ${c.border}`,
    };
  },

  statusBadge(status: string): CSSProperties {
    const map: Record<string, { bg: string; color: string }> = {
      DRAFT:              { bg: "#f3f4f6", color: "#6b7280" },
      REQUIREMENTS_READY: { bg: "#e0f2fe", color: "#0369a1" },
      SPEC_READY:         { bg: "#ede9fe", color: "#5b21b6" },
      GENERATING:         { bg: "#fef3c7", color: "#b45309" },
      GENERATED:          { bg: "#f0fdf4", color: "#15803d" },
      REVIEW:             { bg: "#dbeafe", color: "#1d4ed8" },
      DEPLOYED:           { bg: "#dcfce7", color: "#15803d" },
    };
    const c = map[status] ?? { bg: "#f3f4f6", color: "#6b7280" };
    return {
      display: "inline-block",
      padding: "0.175rem 0.55rem",
      borderRadius: "4px",
      fontSize: "0.6875rem",
      fontWeight: 600,
      letterSpacing: "0.04em",
      textTransform: "uppercase",
      background: c.bg,
      color: c.color,
    };
  },
};

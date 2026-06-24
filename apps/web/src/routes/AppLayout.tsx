import { Braces, Cpu, FolderKanban, LogOut, Moon, Plus, Sun, UserRound } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../features/auth/auth-context";
import { useTheme } from "../features/theme/theme-context";

export function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      {/* ── Desktop sidebar ─────────────────────────────────────── */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-zinc-800 bg-zinc-950 px-5 py-6 lg:flex lg:flex-col">
        <Link to="/" className="flex items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-md bg-emerald-400 text-zinc-950">
            <Braces size={20} strokeWidth={2.6} />
          </span>
          <span>
            <span className="block text-xs font-bold uppercase tracking-widest text-emerald-400">
              ProgresIA
            </span>
            <span className="block text-xs text-zinc-500">Studio</span>
          </span>
        </Link>

        <div className="mt-8 border-t border-zinc-800" />

        <nav className="mt-5 grid gap-1" aria-label="Navegación principal">
          <NavLink className="nav-link" to="/" end>
            <FolderKanban size={17} />
            Proyectos
          </NavLink>
          <NavLink className="nav-link" to="/projects/new">
            <Plus size={17} />
            Nuevo proyecto
          </NavLink>
          <NavLink className="nav-link" to="/ai-settings">
            <Cpu size={17} />
            Configuración IA
          </NavLink>
        </nav>

        {/* User at bottom of sidebar */}
        <div className="mt-auto border-t border-zinc-800 pt-5">
          <div className="flex items-center gap-2.5 rounded-md px-2 py-1.5">
            <div className="grid size-7 shrink-0 place-items-center rounded-full border border-zinc-700 bg-zinc-800 text-xs font-semibold text-zinc-300">
              {(auth.user?.name ?? "U")[0]?.toUpperCase()}
            </div>
            <span className="min-w-0 flex-1 truncate text-xs text-zinc-400">
              {auth.user?.name ?? "Usuario"}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main area ───────────────────────────────────────────── */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/95 px-5 py-3 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
            {/* Mobile logo */}
            <Link to="/" className="flex items-center gap-2 lg:hidden">
              <Braces className="text-emerald-400" size={18} />
              <span className="text-sm font-bold tracking-tight">ProgresIA Studio</span>
            </Link>

            {/* Desktop breadcrumb */}
            <div className="hidden text-xs font-medium uppercase tracking-widest text-zinc-600 lg:block">
              Workspace
            </div>

            <div className="flex items-center gap-2">
              {/* Desktop user chip */}
              <div className="hidden items-center gap-2 rounded-md border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 sm:flex">
                <UserRound size={13} />
                {auth.user?.name ?? "Usuario"}
              </div>

              <button
                className="icon-button"
                title={theme === "dark" ? "Tema claro" : "Tema oscuro"}
                aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
                onClick={toggle}
              >
                {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              </button>

              <button
                className="icon-button"
                title="Cerrar sesión"
                aria-label="Cerrar sesión"
                onClick={() => {
                  auth.logout();
                  navigate("/login");
                }}
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </header>

        {/* Page content — extra bottom padding on mobile for bottom nav */}
        <main className="mx-auto max-w-7xl px-5 py-8 pb-28 lg:pb-8">
          <Outlet />
        </main>
      </div>

      {/* ── Mobile bottom navigation ─────────────────────────────── */}
      <nav
        className="fixed bottom-0 inset-x-0 z-10 border-t border-zinc-800 bg-zinc-950/95 backdrop-blur lg:hidden"
        aria-label="Navegación móvil"
      >
        <div className="flex">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
                isActive ? "text-emerald-400" : "text-zinc-500 hover:text-zinc-300"
              }`
            }
          >
            <FolderKanban size={20} />
            Proyectos
          </NavLink>
          <NavLink
            to="/projects/new"
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
                isActive ? "text-emerald-400" : "text-zinc-500 hover:text-zinc-300"
              }`
            }
          >
            <Plus size={20} />
            Nuevo
          </NavLink>
          <NavLink
            to="/ai-settings"
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
                isActive ? "text-emerald-400" : "text-zinc-500 hover:text-zinc-300"
              }`
            }
          >
            <Cpu size={20} />
            IA
          </NavLink>
        </div>
      </nav>
    </div>
  );
}

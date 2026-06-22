import { Braces, FolderKanban, LogOut, Moon, Plus, Sun, UserRound } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../features/auth/auth-context";
import { useTheme } from "../features/theme/theme-context";

export function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-zinc-800 bg-zinc-950 px-5 py-6 lg:block">
        <Link to="/" className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-md bg-emerald-400 text-zinc-950">
            <Braces size={20} strokeWidth={2.6} />
          </span>
          <span>
            <span className="block text-xs font-bold uppercase tracking-widest text-emerald-400">
              ProgresIA
            </span>
            <span className="block text-xs text-zinc-500">Studio</span>
          </span>
        </Link>

        <nav className="mt-10 grid gap-1">
          <NavLink className="nav-link" to="/">
            <FolderKanban size={17} />
            Proyectos
          </NavLink>
          <NavLink className="nav-link" to="/projects/new">
            <Plus size={17} />
            Nuevo proyecto
          </NavLink>
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/95 px-5 py-3 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
            <Link to="/" className="flex items-center gap-2 lg:hidden">
              <Braces className="text-emerald-400" size={18} />
              <span className="text-sm font-bold tracking-tight">ProgresIA Studio</span>
            </Link>
            <div className="hidden text-xs font-medium uppercase tracking-widest text-zinc-600 lg:block">
              Workspace
            </div>
            <div className="flex items-center gap-2">
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
                title="Cerrar sesion"
                aria-label="Cerrar sesion"
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
        <main className="mx-auto max-w-7xl px-5 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

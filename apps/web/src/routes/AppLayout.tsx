import { Braces, FolderKanban, LogOut, Plus, UserRound } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../features/auth/auth-context";

export function AppLayout() {
  const auth = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-zinc-950 px-4 py-5 lg:block">
        <Link to="/" className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-md bg-emerald-400 text-zinc-950">
            <Braces size={22} strokeWidth={2.4} />
          </span>
          <span>
            <span className="block text-sm font-semibold uppercase text-emerald-300">ProgresIA</span>
            <span className="block text-sm text-zinc-400">Studio</span>
          </span>
        </Link>

        <nav className="mt-8 grid gap-2">
          <NavLink className="nav-link" to="/">
            <FolderKanban size={18} />
            Proyectos
          </NavLink>
          <NavLink className="nav-link" to="/projects/new">
            <Plus size={18} />
            Nuevo proyecto
          </NavLink>
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-white/10 bg-zinc-950/90 px-5 py-4 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
            <Link to="/" className="flex items-center gap-2 font-semibold lg:hidden">
              <Braces className="text-emerald-300" size={20} />
              ProgresIA Studio
            </Link>
            <div className="hidden text-sm text-zinc-400 lg:block">Workspace operativo</div>
            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm text-zinc-300 sm:flex">
                <UserRound size={16} />
                {auth.user?.name ?? "Usuario"}
              </div>
              <button
                className="icon-button"
                title="Cerrar sesion"
                aria-label="Cerrar sesion"
                onClick={() => {
                  auth.logout();
                  navigate("/login");
                }}
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-5 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

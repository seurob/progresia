import { Navigate, Outlet } from "react-router";
import { useAuth } from "../features/auth/auth-context";

export function ProtectedRoute() {
  const auth = useAuth();

  // Hold render while verifying the stored token against the API.
  // Prevents a flash of authenticated content when the token is stale.
  if (auth.isLoading) {
    return <div className="min-h-screen bg-zinc-950" aria-hidden="true" />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

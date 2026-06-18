import { Navigate, Outlet } from "react-router";
import { useAuth } from "../features/auth/auth-context";

export function ProtectedRoute() {
  const auth = useAuth();

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

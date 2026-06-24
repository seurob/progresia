import { useState } from "react";
import { ADMIN_CSS } from "./adminStyles";
import { AdminDashboard } from "./AdminDashboard";
import { AdminLoginForm } from "./AdminLoginForm";

const STORAGE_KEY = "admin_access_token";

export function AdminPage() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(STORAGE_KEY));

  function handleLogin(newToken: string) {
    sessionStorage.setItem(STORAGE_KEY, newToken);
    setToken(newToken);
  }

  function handleLogout() {
    sessionStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }

  return (
    <>
      <style>{ADMIN_CSS}</style>
      {!token
        ? <AdminLoginForm onLogin={handleLogin} />
        : <AdminDashboard token={token} onLogout={handleLogout} />
      }
    </>
  );
}

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:3000/api";

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  createdAt: string;
  updatedAt: string;
}

export interface AdminProject {
  id: string;
  name: string;
  slug: string;
  sector: string;
  productType: string;
  description: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  workspace?: {
    owner?: { id: string; name: string; email: string };
  };
}

async function apiFetch<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}/admin${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {})
    }
  });

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { message?: string | string[] };
    const msg = Array.isArray(err.message) ? err.message.join("; ") : (err.message ?? `Error ${res.status}`);
    throw new Error(msg);
  }

  return res.status === 204 ? (null as T) : (res.json() as Promise<T>);
}

export const adminApi = {
  login: (identifier: string, password: string) =>
    apiFetch<{ accessToken: string; user: AdminUser }>("/auth/login", null, {
      method: "POST",
      body: JSON.stringify({ identifier, password })
    }),

  me: (token: string) => apiFetch<AdminUser>("/auth/me", token),

  getUsers: (token: string, search?: string) =>
    apiFetch<AdminUser[]>(
      `/users${search ? `?search=${encodeURIComponent(search)}` : ""}`,
      token
    ),

  createUser: (token: string, data: { name: string; email: string; password: string; role: string }) =>
    apiFetch<AdminUser>("/users", token, {
      method: "POST",
      body: JSON.stringify(data)
    }),

  updateUser: (
    token: string,
    id: string,
    data: Partial<{ name: string; email: string; password: string; role: string }>
  ) =>
    apiFetch<AdminUser>(`/users/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(data)
    }),

  deleteUser: (token: string, id: string) =>
    apiFetch<null>(`/users/${id}`, token, { method: "DELETE" }),

  getProjects: (token: string, search?: string) =>
    apiFetch<AdminProject[]>(
      `/projects${search ? `?search=${encodeURIComponent(search)}` : ""}`,
      token
    ),

  createProject: (
    token: string,
    data: { name: string; sector: string; productType: string; description: string; ownerId: string }
  ) =>
    apiFetch<AdminProject>("/projects", token, {
      method: "POST",
      body: JSON.stringify(data)
    }),

  updateProject: (
    token: string,
    id: string,
    data: Partial<{ name: string; sector: string; productType: string; description: string; status: string }>
  ) =>
    apiFetch<AdminProject>(`/projects/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(data)
    }),

  deleteProject: (token: string, id: string) =>
    apiFetch<null>(`/projects/${id}`, token, { method: "DELETE" })
};

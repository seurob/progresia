import axios from "axios";
import { clearAllTokens, getAccessToken, getRefreshToken, setAccessToken, setRefreshToken } from "./auth-token";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:3000/api"
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let _logoutHandler: (() => void) | null = null;
let _refreshing: Promise<string> | null = null;

export function registerLogout(fn: () => void) {
  _logoutHandler = fn;
}

async function attemptTokenRefresh(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error("No refresh token");

  const res = await axios.post<{ accessToken: string; refreshToken: string }>(
    `${api.defaults.baseURL}/auth/refresh`,
    { refreshToken }
  );

  setAccessToken(res.data.accessToken);
  setRefreshToken(res.data.refreshToken);
  return res.data.accessToken;
}

api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) {
      throw error;
    }

    // Avoid retry loop on the refresh endpoint itself
    const url = error.config?.url ?? "";
    if (url.includes("/auth/refresh") || url.includes("/auth/login")) {
      _logoutHandler?.();
      throw error;
    }

    try {
      _refreshing ??= attemptTokenRefresh().finally(() => { _refreshing = null; });
      const newToken = await _refreshing;

      if (error.config) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return api.request(error.config);
      }
    } catch {
      clearAllTokens();
      _logoutHandler?.();
    }

    throw error;
  }
);

export function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.message;
    return Array.isArray(message) ? message.join(", ") : message ?? error.message;
  }

  return "No se pudo completar la operacion.";
}

import { createContext, useContext } from "react";
import { User } from "../../types/api";

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user?: User;
  token: string | null;
  setSession: (accessToken: string, user: User, refreshToken?: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

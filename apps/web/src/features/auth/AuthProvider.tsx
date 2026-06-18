import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactNode, useMemo, useState } from "react";
import { clearAccessToken, getAccessToken, setAccessToken } from "../../lib/auth-token";
import { api } from "../../lib/api";
import { User } from "../../types/api";
import { AuthContext, AuthContextValue } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => getAccessToken());

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const response = await api.get<User>("/users/me");
      return response.data;
    },
    enabled: Boolean(token),
    retry: false
  });

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      isLoading: meQuery.isLoading,
      user: meQuery.data,
      token,
      setSession: (newToken, user) => {
        setAccessToken(newToken);
        setToken(newToken);
        queryClient.setQueryData(["me"], user);
      },
      logout: () => {
        clearAccessToken();
        setToken(null);
        queryClient.clear();
      }
    }),
    [meQuery.data, meQuery.isLoading, queryClient, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

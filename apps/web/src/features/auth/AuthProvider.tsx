import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { clearAllTokens, getAccessToken, setAccessToken, setRefreshToken } from "../../lib/auth-token";
import { api, registerLogout } from "../../lib/api";
import { User } from "../../types/api";
import { AuthContext, AuthContextValue } from "./auth-context";

export function AuthProvider({ children }: { readonly children: ReactNode }) {
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
      setSession: (accessToken, user, refreshToken) => {
        setAccessToken(accessToken);
        if (refreshToken) setRefreshToken(refreshToken);
        setToken(accessToken);
        queryClient.setQueryData(["me"], user);
      },
      logout: () => {
        clearAllTokens();
        setToken(null);
        queryClient.clear();
      }
    }),
    [meQuery.data, meQuery.isLoading, queryClient, token]
  );

  useEffect(() => {
    registerLogout(value.logout);
  }, [value.logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

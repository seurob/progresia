import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { AuthContext, AuthContextValue } from "../features/auth/auth-context";
import { ProtectedRoute } from "../components/ProtectedRoute";

function makeAuthContext(partial: Partial<AuthContextValue>): AuthContextValue {
  return {
    isAuthenticated: false,
    isLoading: false,
    user: undefined,
    token: null,
    setSession: vi.fn(),
    logout: vi.fn(),
    ...partial
  };
}

function renderWithRouter(
  auth: AuthContextValue,
  initialPath: string
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={[initialPath]}>
          <Routes>
            <Route path="/login" element={<p>Login page</p>} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<p>Dashboard</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users to /login", () => {
    renderWithRouter(makeAuthContext({ isAuthenticated: false }), "/");
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders children for authenticated users", () => {
    renderWithRouter(
      makeAuthContext({ isAuthenticated: true, token: "tok" }),
      "/"
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("does not render dashboard when unauthenticated", () => {
    renderWithRouter(makeAuthContext({ isAuthenticated: false }), "/");
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AuthContext, AuthContextValue } from "../features/auth/auth-context";
import { NewProjectPage } from "../routes/NewProjectPage";

vi.mock("../lib/api", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [{ id: "ws-1", name: "Mi workspace" }] }),
    post: vi.fn().mockResolvedValue({ data: { id: "proj-1", name: "Test Project" } })
  },
  getErrorMessage: vi.fn((e: unknown) => String(e))
}));

import * as apiModule from "../lib/api";

const auth: AuthContextValue = {
  isAuthenticated: true,
  isLoading: false,
  user: { id: "u1", email: "test@test.com", name: "Test", role: "OWNER", createdAt: "", updatedAt: "" },
  token: "tok",
  setSession: vi.fn(),
  logout: vi.fn()
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={["/projects/new"]}>
          <Routes>
            <Route path="/projects/new" element={<NewProjectPage />} />
            <Route path="/projects/:id" element={<p>Project detail</p>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe("NewProjectPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiModule.api.get).mockResolvedValue({ data: [{ id: "ws-1", name: "Mi workspace" }] } as never);
    vi.mocked(apiModule.api.post).mockResolvedValue({ data: { id: "proj-1", name: "Test Project" } } as never);
  });

  it("renders the new project form", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: /Define el contenedor/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Crear proyecto/i })).toBeInTheDocument();
  });

  it("submit button is present and enabled", () => {
    renderPage();
    const submit = screen.getByRole("button", { name: /Crear proyecto/i });
    expect(submit).toBeInTheDocument();
    expect(submit).not.toBeDisabled();
  });

  it("loads workspace options from API", async () => {
    renderPage();
    await waitFor(() => {
      expect(vi.mocked(apiModule.api.get)).toHaveBeenCalledWith("/workspaces");
    });
  });

  it("navigates to project detail after successful creation", async () => {
    renderPage();
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/Reservas de clases/i), "Proyecto Test");
    await user.type(screen.getByPlaceholderText(/Educacion/i), "Tecnologia");
    await user.type(screen.getByPlaceholderText(/Plataforma para gestionar/i), "Descripcion suficientemente larga del proyecto");

    await user.click(screen.getByRole("button", { name: /Crear proyecto/i }));

    await waitFor(() => {
      expect(screen.getByText("Project detail")).toBeInTheDocument();
    });
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./features/auth/AuthProvider";
import { ThemeProvider } from "./features/theme/ThemeProvider";
import { AppLayout } from "./routes/AppLayout";
import { AuthPage } from "./routes/AuthPage";
import { DashboardPage } from "./routes/DashboardPage";
import { NewProjectPage } from "./routes/NewProjectPage";
import { ProjectDetailPage } from "./routes/ProjectDetailPage";
import { AdminPage } from "./routes/admin/AdminPage";
import { AiSettingsPage } from "./routes/AiSettingsPage";
import { NotFoundPage } from "./routes/NotFoundPage";
import "./styles.css";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/gestion-usuarios",
    element: <AdminPage />
  },
  {
    path: "/login",
    element: <AuthPage mode="login" />
  },
  {
    path: "/register",
    element: <AuthPage mode="register" />
  },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <DashboardPage />
          },
          {
            path: "projects/new",
            element: <NewProjectPage />
          },
          {
            path: "projects/:projectId",
            element: <ProjectDetailPage />
          },
          {
            path: "ai-settings",
            element: <AiSettingsPage />
          }
        ]
      }
    ]
  },
  {
    path: "*",
    element: <NotFoundPage />
  }
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);

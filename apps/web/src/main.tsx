import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./features/auth/AuthProvider";
import { AppLayout } from "./routes/AppLayout";
import { AuthPage } from "./routes/AuthPage";
import { DashboardPage } from "./routes/DashboardPage";
import { NewProjectPage } from "./routes/NewProjectPage";
import { ProjectDetailPage } from "./routes/ProjectDetailPage";
import "./styles.css";

const queryClient = new QueryClient();

const router = createBrowserRouter([
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
          }
        ]
      }
    ]
  }
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);

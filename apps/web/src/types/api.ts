export type Role = "ADMIN" | "OWNER" | "COLLABORATOR" | "REVIEWER";

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  accessToken: string;
  user: User;
}

export interface Workspace {
  id: string;
  name: string;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Idea {
  id: string;
  projectId: string;
  problem: string;
  targetUsers: string;
  coreFeatures: string[];
  complexity: string;
  needsAi: boolean;
  needsAuth: boolean;
  needsAdminPanel: boolean;
  constraints?: string | null;
}

export interface Specification {
  id: string;
  projectId: string;
  type: "REQUIREMENTS" | "OPENSPEC" | "ARCHITECTURE" | "DATA_MODEL";
  status: "DRAFT" | "GENERATED" | "APPROVED" | "REJECTED";
  content: Record<string, unknown>;
  createdAt: string;
}

export interface Project {
  id: string;
  workspaceId: string;
  name: string;
  sector: string;
  productType: string;
  description: string;
  status: "DRAFT" | "SPEC_READY" | "GENERATING" | "GENERATED" | "REVIEW" | "DEPLOYED";
  createdAt: string;
  updatedAt: string;
  idea?: Idea | null;
  specifications?: Specification[];
}

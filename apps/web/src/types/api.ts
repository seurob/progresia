export type Role = "ADMIN" | "OWNER" | "COLLABORATOR" | "REVIEWER";

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  emailVerified?: boolean;
  accountStatus?: "PENDING_VERIFICATION" | "ACTIVE" | "SUSPENDED" | "DELETED";
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface RegisterPendingResponse {
  requiresEmailVerification: true;
  email: string;
  message: string;
}

export interface WorkspaceMember {
  id: string;
  workspaceId: string;
  userId: string;
  role: Role;
  createdAt: string;
  user: { id: string; name: string; email: string };
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

export interface RequirementItem {
  id: string;
  title: string;
  description: string;
}

export interface UserStory {
  id: string;
  actor: string;
  goal: string;
  benefit: string;
}

export interface RequirementsContent {
  project_name: string;
  functional_requirements: RequirementItem[];
  non_functional_requirements: RequirementItem[];
  user_stories: UserStory[];
}

export interface TechProposal {
  id: number;
  name: string;
  tagline: string;
  stack: string[];
  difficulty: string;
  description: string;
  advantages: string[];
  limitations: string[];
  recommended_for: string;
  learning_outcomes: string[];
  docker_ready: boolean;
  ai_ready: boolean;
  estimated_setup_minutes: number;
}

export interface TechProposalContent {
  proposals: TechProposal[];
  recommended_id: number;
  recommendation_reason: string;
}

export interface Specification {
  id: string;
  projectId: string;
  type: "REQUIREMENTS" | "OPENSPEC" | "ARCHITECTURE" | "DATA_MODEL" | "ISSUES" | "TUTORIAL" | "CODE" | "TECH_PROPOSAL";
  status: "DRAFT" | "GENERATED" | "APPROVED" | "REJECTED";
  content: Record<string, unknown>;
  createdAt: string;
}

export interface GeneratedFile {
  path: string;
  language: string;
  content: string;
}

export interface PushToGithubResult {
  repoUrl: string;
  cloneUrl: string;
  commitSha: string;
}

export interface ArtifactBundle {
  id: string;
  projectId: string;
  specificationId: string;
  status: "GENERATED" | "EXPORTED";
  manifest: Record<string, unknown>;
  generatedContent?: { project_name: string; files: GeneratedFile[] } | null;
  createdAt: string;
}

export interface JobStatus {
  id: string | undefined;
  name: string;
  status: "waiting" | "active" | "completed" | "failed" | "delayed" | "paused";
  progress: unknown;
  result?: unknown;
  failReason?: string;
}

export interface Project {
  id: string;
  workspaceId: string;
  name: string;
  slug: string;
  sector: string;
  productType: string;
  description: string;
  status: "DRAFT" | "REQUIREMENTS_READY" | "SPEC_READY" | "GENERATING" | "GENERATED" | "REVIEW" | "DEPLOYED";
  createdAt: string;
  updatedAt: string;
  idea?: Idea | null;
  specifications?: Specification[];
  artifactBundles?: ArtifactBundle[];
}

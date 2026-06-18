export type AiJobName = "generate-requirements" | "generate-openspec" | "generate-code";

export interface AiJobData {
  userId: string;
  projectId: string;
}

export const AI_QUEUE = "ai-jobs";

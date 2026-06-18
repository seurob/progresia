export interface HealthResponse {
  status: "ok";
  service: string;
  timestamp: string;
}

export interface IdeaInput {
  name: string;
  sector: string;
  problem: string;
  targetUsers: string;
  coreFeatures: string[];
}

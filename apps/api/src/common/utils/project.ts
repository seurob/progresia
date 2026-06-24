/** Maps idea.complexity (DB: "simple" | "standard" | "complex") to the technical_level expected by the AI service. */
export function complexityToLevel(complexity: string | null | undefined): string {
  if (complexity === "simple") return "BEGINNER";
  if (complexity === "complex") return "ADVANCED";
  return "INTERMEDIATE";
}

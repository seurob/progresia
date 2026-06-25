import { render, screen } from "@testing-library/react";
import { ModelControls } from "./ModelControls";

const providers = [
  { name: "groq" as const, has_key: true, model: "groq-model", default_model: "groq-model" },
  { name: "openai" as const, has_key: true, model: "openai-model", default_model: "openai-model" },
  { name: "gemini" as const, has_key: true, model: "gemini-model", default_model: "gemini-model" },
  {
    name: "ollama" as const,
    has_key: true,
    model: "gemma4:26b-a4b-it-qat",
    default_model: "gemma4:26b-a4b-it-qat",
    code_model: "gemma4:26b-a4b-it-qat",
    default_code_model: "gemma4:26b-a4b-it-qat",
  },
];

it("shows recommended Gemma models even when they are not installed", () => {
  render(
    <ModelControls
      cloudOrder={["groq", "openai", "gemini"]}
      providers={providers}
      providerModels={{}}
      ollamaModels={[]}
      modelDrafts={{}}
      onCloudOrderChange={() => undefined}
      onModelChange={() => undefined}
    />,
  );

  expect(screen.getAllByRole("option", { name: "gemma4:26b-a4b-it-qat" })).toHaveLength(2);
  expect(screen.getAllByRole("option", { name: "gemma4:31b" })).toHaveLength(2);
});

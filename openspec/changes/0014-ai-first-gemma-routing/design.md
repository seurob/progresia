# Design

`get_llm_candidates()` returns configured models in execution order instead of
only the first constructible client. Technology decisions request Ollama first,
then cloud providers. Code generation follows its task-specific Ollama-first
chain.

Each AI result is validated. Invalid architecture, malformed output or runtime
failure advances to the next candidate. Deterministic catalogs and
`FallbackGenerator` execute only after every AI candidate fails.

The default local profile is `gemma4:26b-a4b`. Users with a strong GPU or
abundant RAM can set both Ollama model variables to `gemma4:31b`.

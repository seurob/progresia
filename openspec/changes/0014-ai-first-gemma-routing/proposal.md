# Proposal: AI-first technology and code generation

## Motivation

Technology proposals and code generation must exhaust configured AI providers
before using deterministic catalogs or scaffold templates. Local Ollama profiles
should support a balanced computer and a high-capacity workstation.

## Scope

- Add Gemma 4 Ollama profiles and installation commands.
- Prefer local Ollama for technology decisions.
- Retry all available AI candidates after invocation or validation failures.
- Keep deterministic catalogs and scaffold templates as the final fallback.
- Preserve architecture validation for web, mobile, desktop and Django choices.

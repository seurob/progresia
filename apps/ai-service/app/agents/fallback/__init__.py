"""Fallback scaffold system for CodeGenerationAgent.

When the LLM fails to generate a valid code scaffold, this module provides
a deterministic, stack-aware fallback that generates a complete, runnable
project scaffold.
"""
from app.agents.fallback.generator import FallbackGenerator

__all__ = ["FallbackGenerator"]

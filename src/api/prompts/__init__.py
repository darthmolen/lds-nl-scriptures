"""Prompt templates for LLM-powered features.

This module provides system prompts and prompt builders for the
scripture assistant RAG system.
"""

from src.api.prompts.scripture_assistant import SYSTEM_PROMPT, build_user_prompt

__all__ = ["SYSTEM_PROMPT", "build_user_prompt"]

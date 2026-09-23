"""LLM abstraction layer — full implementation.

Provides a unified ``LLMGenerator`` class that dispatches to one of four
provider adapters based on ``settings.LLM_PROVIDER``:
  - ``openai``  — openai.AsyncOpenAI
  - ``groq``    — groq.AsyncGroq
  - ``gemini``  — google.generativeai (sync, wrapped in executor)
  - ``ollama``  — httpx POST to /api/chat
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import List

import httpx
import structlog

from app.core.config import Settings
from app.rag.generation.prompts import SYSTEM_PROMPT, build_context_prompt
from app.rag.retrieval.bm25 import RetrievedChunk

log = structlog.get_logger(__name__)


# --------------------------------------------------------------------------- #
# Result data-class
# --------------------------------------------------------------------------- #


@dataclass
class GenerationResult:
    """Result of a single LLM generation call."""

    answer: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    provider: str


# --------------------------------------------------------------------------- #
# LLMGenerator
# --------------------------------------------------------------------------- #


class LLMGenerator:
    """Unified LLM interface; dispatches to the configured provider.

    Parameters
    ----------
    settings:
        Application settings object.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        max_tokens: int = 1024,
    ) -> GenerationResult:
        """Build prompt from chunks and call the configured LLM.

        Returns a :class:`GenerationResult` with the answer text and token
        usage metadata.
        """
        user_message = build_context_prompt(query, chunks)
        provider = self.settings.LLM_PROVIDER.lower()

        log.info(
            "llm.generate",
            provider=provider,
            model=self.settings.LLM_MODEL,
            num_chunks=len(chunks),
        )

        if provider == "openai":
            return await self._call_openai(user_message, max_tokens)
        if provider == "groq":
            return await self._call_groq(user_message, max_tokens)
        if provider == "gemini":
            return await self._call_gemini(user_message, max_tokens)
        if provider == "ollama":
            return await self._call_ollama(user_message, max_tokens)

        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")

    # ---------------------------------------------------------------------- #
    # Provider implementations
    # ---------------------------------------------------------------------- #

    async def _call_openai(self, user_message: str, max_tokens: int) -> GenerationResult:
        """Call the OpenAI Chat Completions API."""
        import openai  # noqa: PLC0415

        client = openai.AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=self.settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        choice = response.choices[0]
        usage = response.usage
        return GenerationResult(
            answer=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            model=self.settings.LLM_MODEL,
            provider="openai",
        )

    async def _call_groq(self, user_message: str, max_tokens: int) -> GenerationResult:
        """Call the Groq Chat API (OpenAI-compatible interface)."""
        import groq  # noqa: PLC0415

        client = groq.AsyncGroq(api_key=self.settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=self.settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        choice = response.choices[0]
        usage = response.usage
        return GenerationResult(
            answer=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            model=self.settings.LLM_MODEL,
            provider="groq",
        )

    async def _call_gemini(self, user_message: str, max_tokens: int) -> GenerationResult:
        """Call Google Generative AI (Gemini) — sync SDK wrapped in executor."""
        import google.generativeai as genai  # noqa: PLC0415

        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=self.settings.LLM_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.0,
        )

        def _sync_call() -> genai.types.GenerateContentResponse:  # type: ignore[name-defined]
            return model.generate_content(
                user_message,
                generation_config=generation_config,
            )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_call)
        answer = response.text or ""
        # Gemini doesn't always expose token counts in the same way
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
        return GenerationResult(
            answer=answer,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self.settings.LLM_MODEL,
            provider="gemini",
        )

    async def _call_ollama(self, user_message: str, max_tokens: int) -> GenerationResult:
        """Call a local Ollama instance via its HTTP /api/chat endpoint."""
        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.0},
        }
        url = f"{self.settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        message = data.get("message", {})
        answer = message.get("content", "")
        # Ollama returns eval_count (completion tokens) and prompt_eval_count
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        return GenerationResult(
            answer=answer,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self.settings.LLM_MODEL,
            provider="ollama",
        )

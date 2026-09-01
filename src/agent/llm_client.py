"""LLM client supporting live Google GenAI or OpenAI calls.

Production evaluation deliberately has no scenario-aware offline fallback. A benchmark
must fail transparently when every configured live model is unavailable instead of
substituting hard-coded answers and reporting them as agent results. Provider-level
failover remains live-model reasoning and is recorded on every run.
"""

import json
import os
import re
import time
from typing import Any, Dict, Optional, Tuple


class LLMClientError(RuntimeError):
    """Raised when no configured live model can produce a valid response."""


class LLMClient:
    """Provides a small, auditable interface to configured live models."""

    def __init__(self, model_name: Optional[str] = None, generation_seed: int = 42):
        self.model_name = model_name or os.environ.get("MODEL_NAME", "gemini-3.6-flash")
        self.generation_seed = generation_seed
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in {
            "1",
            "true",
            "yes",
        }
        self.vertex_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.vertex_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
        self.call_count = 0
        self.token_count = 0
        self.estimated_cost_usd = 0.0
        self.last_provider: Optional[str] = None
        self.last_model: Optional[str] = None
        self.last_error: Optional[str] = None
        self.max_attempts = max(1, int(os.environ.get("MODEL_MAX_ATTEMPTS", "2")))
        self.fallback_attempts = max(1, int(os.environ.get("MODEL_FALLBACK_ATTEMPTS", "1")))
        self.retry_backoff_seconds = max(
            0.0, float(os.environ.get("MODEL_RETRY_BACKOFF_SECONDS", "1.0"))
        )
        self.gemini_fallback_model = os.environ.get(
            "GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite"
        ).strip()

    def is_live_model_available(self) -> bool:
        return bool(self.gemini_key or (self.use_vertex and self.vertex_project) or self.openai_key)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extracts JSON object from markdown or raw text."""
        text = text.strip()
        # Remove code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Extract outer JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)

    def complete_json(self, prompt: str, system_instruction: str = "") -> Tuple[Dict[str, Any], int]:
        """Calls the configured LLM and returns parsed JSON and token count."""
        errors = []

        # 1. Try Gemini when configured. A second *live Gemini model* is allowed as
        # a provider-level resilience boundary. This is not an offline or
        # scenario-aware fallback; the successful model is recorded in evidence.
        if self.gemini_key or (self.use_vertex and self.vertex_project):
            primary_model = (
                self.model_name
                if not self.model_name.lower().startswith("gpt")
                else os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
            )
            gemini_models = [primary_model]
            if self.gemini_fallback_model and self.gemini_fallback_model != primary_model:
                gemini_models.append(self.gemini_fallback_model)

            stop_gemini_failover = False
            for model_index, gemini_model in enumerate(gemini_models):
                attempts = self.max_attempts if model_index == 0 else self.fallback_attempts
                for attempt in range(1, attempts + 1):
                    try:
                        from google import genai
                        from google.genai import types

                        if self.use_vertex and self.vertex_project:
                            client = genai.Client(
                                vertexai=True,
                                project=self.vertex_project,
                                location=self.vertex_location,
                                http_options=types.HttpOptions(timeout=60_000),
                            )
                        else:
                            client = genai.Client(
                                api_key=self.gemini_key,
                                http_options=types.HttpOptions(timeout=60_000),
                            )
                        full_prompt = f"{prompt}\n\nRespond ONLY with a valid JSON object."
                        self.call_count += 1
                        response = client.models.generate_content(
                            model=gemini_model,
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.1,
                                seed=self.generation_seed,
                                max_output_tokens=2_048,
                                response_mime_type="application/json",
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                            ),
                        )
                        if response.text:
                            parsed = self._extract_json(response.text)
                            usage = getattr(response, "usage_metadata", None)
                            tokens = int(getattr(usage, "total_token_count", 0) or 0)
                            self.token_count += tokens
                            self.last_provider = "google"
                            self.last_model = gemini_model
                            self.last_error = None
                            return parsed, tokens
                        raise LLMClientError("Gemini returned an empty response")
                    except Exception as e:
                        detail = (
                            f"Gemini model {gemini_model} failed "
                            f"(attempt {attempt}/{attempts}): {type(e).__name__}: {e}"
                        )
                        errors.append(detail)
                        retryable = self._is_retryable(e)
                        if attempt < attempts and retryable:
                            time.sleep(self.retry_backoff_seconds * attempt)
                            continue
                        if not self._can_try_model_fallback(e):
                            stop_gemini_failover = True
                        break
                if stop_gemini_failover:
                    break

        # 2. Try OpenAI only when separately configured.
        if self.openai_key:
            for attempt in range(1, self.max_attempts + 1):
              try:
                from openai import OpenAI

                client = OpenAI(api_key=self.openai_key, timeout=10.0)
                openai_model = self.model_name if self.model_name.lower().startswith("gpt") else os.environ.get(
                    "OPENAI_MODEL", "gpt-4o"
                )
                self.call_count += 1
                response = client.chat.completions.create(
                    model=openai_model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                content = response.choices[0].message.content or "{}"
                parsed = self._extract_json(content)
                tokens = int(response.usage.total_tokens if response.usage else 0)
                self.token_count += tokens
                self.last_provider = "openai"
                self.last_model = openai_model
                self.last_error = None
                return parsed, tokens
              except Exception as e:
                detail = f"OpenAI request failed (attempt {attempt}/{self.max_attempts}): {type(e).__name__}: {e}"
                if attempt < self.max_attempts and self._is_retryable(e):
                    time.sleep(1.0)
                    continue
                errors.append(detail)
                break

        if not errors:
            errors.append("No live model API key is configured")
        self.last_error = " | ".join(errors)
        raise LLMClientError(self.last_error)

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Return whether a provider error is plausibly transient.

        Retry is deliberately bounded to one extra attempt. Authentication,
        permission, not-found, and other permanent 4xx failures fail fast.
        """
        if isinstance(error, json.JSONDecodeError):
            return True

        message = f"{type(error).__name__}: {error}".lower()
        permanent_markers = (
            "400",
            "401",
            "403",
            "404",
            "invalid_argument",
            "unauthenticated",
            "permission_denied",
            "generate_content_free_tier_requests",
        )
        if any(marker in message for marker in permanent_markers):
            return False
        transient_markers = (
            "408",
            "429",
            "500",
            "502",
            "503",
            "504",
            "deadline",
            "timeout",
            "temporarily unavailable",
            "resource_exhausted",
        )
        return any(marker in message for marker in transient_markers)

    @staticmethod
    def _can_try_model_fallback(error: Exception) -> bool:
        """Return whether another live model could plausibly recover the call.

        Authentication and permission errors apply to the credential rather than a
        model, so trying another model would only add latency. Model-specific 4xx
        errors and transient provider failures may recover on the fallback model.
        """

        message = f"{type(error).__name__}: {error}".lower()
        credential_markers = (
            "401",
            "403",
            "unauthenticated",
            "permission_denied",
            "api key not valid",
            "invalid api key",
        )
        return not any(marker in message for marker in credential_markers)

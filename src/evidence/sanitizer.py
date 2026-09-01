"""Sanitizes sensitive environment variables, secrets, and connection strings from logs."""

import os
import re
from typing import Any, Dict, List, Union
from src.evidence.serialization import to_json_safe


class SecretSanitizer:
    """Scans and redacts sensitive environment variable values and credentials."""

    def __init__(self, additional_secrets: List[str] = None):
        self.sensitive_patterns = [
            re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),
            re.compile(r"AIza[a-zA-Z0-9_\-]{30,}", re.IGNORECASE),
            re.compile(r"password=([^\s;]+)", re.IGNORECASE),
            re.compile(r":([a-zA-Z0-9_\-]+)@localhost", re.IGNORECASE),
        ]
        self.secret_values: List[str] = []
        for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "POSTGRES_PASSWORD"]:
            val = os.environ.get(key)
            if val and len(val) >= 4:
                self.secret_values.append(val)
        if additional_secrets:
            self.secret_values.extend(additional_secrets)

    def sanitize_str(self, text: str) -> str:
        """Replaces secrets and credentials with [REDACTED]."""
        if not text:
            return text
        sanitized = text
        for secret in self.secret_values:
            if secret in sanitized:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        for pattern in self.sensitive_patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

    def sanitize_obj(self, obj: Any) -> Any:
        """Recursively sanitizes dictionary, list, or primitive objects."""
        obj = to_json_safe(obj)
        if isinstance(obj, str):
            return self.sanitize_str(obj)
        elif isinstance(obj, dict):
            return {self.sanitize_str(str(k)): self.sanitize_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.sanitize_obj(item) for item in obj]
        return obj

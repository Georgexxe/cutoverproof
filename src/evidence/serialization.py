"""Deterministic conversion of runtime values into JSON-compatible evidence."""

from __future__ import annotations

import base64
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


def to_json_safe(value: Any) -> Any:
    """Return a loss-conscious JSON-compatible representation of ``value``.

    PostgreSQL adapters may return binary, decimal, temporal, or UUID values.
    Those values are valid database evidence but Python's standard JSON encoder
    cannot serialize them directly. Binary text is decoded as UTF-8; arbitrary
    binary data is preserved as an explicit base64 object.
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return {
                "encoding": "base64",
                "data": base64.b64encode(raw).decode("ascii"),
            }
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (UUID, Path)):
        return str(value)
    if isinstance(value, Enum):
        return to_json_safe(value.value)
    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_json_safe(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return to_json_safe(model_dump())
    return str(value)

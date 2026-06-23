from __future__ import annotations

import base64
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID


def to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, UUID):
        return str(value)
    return str(value)

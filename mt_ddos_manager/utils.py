"""
Utility functions
"""

import json
from typing import Any


def safe_json_loads(data: str) -> dict:
    """Safely load JSON data"""
    try:
        return json.loads(data) if data else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def safe_json_dumps(data: Any) -> str:
    """Safely dump JSON data"""
    try:
        return json.dumps(data) if data else '{}'
    except (TypeError, ValueError):
        return '{}'
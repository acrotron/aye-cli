# config.py
from typing import Any, Dict

# Private storage – the leading underscore signals “internal”.
_config: Dict[str, Any] = {}

def get_value(key: str, default: Any = None) -> Any:
    """Return the value for *key* or *default* if the key is missing."""
    return _config.get(key, default)


def set_value(key: str, value: Any) -> None:
    """Store *value* under *key* after a simple validation."""
    if not isinstance(key, str):
        raise TypeError("Configuration key must be a string")
    # You could add more validation here (type checking, range, etc.)
    _config[key] = value



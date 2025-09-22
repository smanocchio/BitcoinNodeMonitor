"""Lightweight fallback for pydantic.BaseSettings used in offline tests."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict


class FieldInfo:
    def __init__(self, default: Any, env: str | None = None) -> None:
        self.default = default
        self.env = env


def Field(default: Any, env: str | None = None) -> FieldInfo:
    return FieldInfo(default=default, env=env)


def validator(*field_names: str, pre: bool | None = None):  # noqa: D401
    def decorator(func: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
        func.__validator_config__ = {"fields": field_names, "pre": pre}
        return func

    return decorator


class BaseSettingsMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: Dict[str, Any]) -> type:
        fields: Dict[str, FieldInfo] = {}
        validators_map: Dict[str, Callable[[Any, Any], Any]] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, FieldInfo):
                fields[key] = value
                namespace[key] = value.default
            elif callable(value) and hasattr(value, "__validator_config__"):
                info = value.__validator_config__
                for field in info["fields"]:
                    validators_map.setdefault(field, value)
        namespace["__fields__"] = fields
        namespace["__validators__"] = validators_map
        return super().__new__(mcls, name, bases, namespace)


class BaseSettings(metaclass=BaseSettingsMeta):
    class Config:
        env_file = None

    def __init__(self, **values: Any) -> None:
        data: Dict[str, Any] = {}
        for field_name, info in self.__fields__.items():
            env = info.env or field_name.upper()
            raw = os.getenv(env)
            value = values.get(field_name, raw if raw is not None else info.default)
            validator = self.__validators__.get(field_name)
            if validator:
                value = validator(self.__class__, value)
            data[field_name] = value
        for key, value in data.items():
            setattr(self, key, value)

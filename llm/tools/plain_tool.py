"""Minimal tool decorator used for agent integrations without LangChain."""

from __future__ import annotations

from typing import Any, Callable


class PlainTool:
    """Wraps a callable and exposes a LangChain-like interface."""

    def __init__(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        self._func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__ or "")
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._func(*args, **kwargs)

    def invoke(self, input_data: Any | None = None) -> Any:
        if input_data is None:
            return self._func()
        if isinstance(input_data, dict):
            return self._func(**input_data)
        if isinstance(input_data, (list, tuple)):
            return self._func(*input_data)
        return self._func(input_data)


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
):
    """Decorator that returns a PlainTool wrapper."""

    def decorator(fn: Callable[..., Any]) -> PlainTool:
        return PlainTool(fn, name=name, description=description)

    if func is None:
        return decorator
    return decorator(func)


__all__ = ["PlainTool", "tool"]

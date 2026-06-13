from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ActionResult:
    ok: bool
    message: str
    events: list = field(default_factory=list)


_REGISTRY: dict[str, Callable] = {}


def register(name: str):
    def decorator(fn):
        _REGISTRY[name] = fn
        return fn
    return decorator


def dispatch(gs, action: str, **kwargs) -> ActionResult:
    handler = _REGISTRY.get(action)
    if handler is None:
        return ActionResult(ok=False, message=f"Unknown action: '{action}'")
    try:
        return handler(gs, **kwargs)
    except Exception as exc:
        return ActionResult(ok=False, message=str(exc))

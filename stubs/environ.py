from typing import Any, TypeVar, Type

T = TypeVar("T")

def config(prefix: str) -> Any: pass
def var(default: str="") -> str: pass
def to_config(klass: Type[T]) -> T: pass

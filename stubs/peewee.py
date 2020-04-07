from typing import Any, Optional, TypeVar, Type, List


class Expression:
    pass


T = TypeVar("T", bound="Model")


class Model:
    id: int

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        pass

    @classmethod
    def get(cls: Type[T], expr: Optional[Expression] = None, **kwargs) -> T:
        pass

    @classmethod
    def get_or_none(cls: Type[T], expr: Optional[Expression] = None, **kwargs) -> T:
        pass

    @classmethod
    def select(self, expr: Optional[Expression] = None):
        pass


# These all do things that MyPy chokes on
def TextField() -> Any:
    pass


def DateTimeField() -> Any:
    pass


def BooleanField() -> Any:
    pass


def ForeignKeyField(key: object, null: bool = None, backref: str = "") -> Any:
    pass

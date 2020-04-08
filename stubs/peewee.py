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


# These all do things that MyPy chokes on, so we're going to treat
# them like methods instead of naming classes
def TextField(unique: bool = False) -> Any:
    pass


def DateTimeField(unique: bool = False) -> Any:
    pass


def BooleanField(unique: bool = False) -> Any:
    pass


def ForeignKeyField(key: object, null: bool = None, backref: str = "") -> Any:
    pass

class IntegrityError(Exception): pass

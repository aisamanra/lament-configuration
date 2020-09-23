from typing import Any, Optional, TypeVar, Type, List


class Expression:
    pass


T = TypeVar("T", bound="Model")


class Model:
    id: int

    class DoesNotExist(Exception):
        pass

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

    def save(self):
        pass

    def delete_instance(self) -> Any:
        pass

    @classmethod
    def alias(cls: Type[T]) -> Type[T]:
        pass

    @classmethod
    def delete(self) -> Any:
        pass


# These all do things that MyPy chokes on, so we're going to treat
# them like methods instead of naming classes
def TextField(default: str = "", unique: bool = False, null: bool = None) -> Any:
    pass


def DateTimeField(unique: bool = False, null: bool = None) -> Any:
    pass


def BooleanField(default: bool = False, unique: bool = False, null: bool = None) -> Any:
    pass


def ForeignKeyField(key: object, null: bool = None, backref: str = "") -> Any:
    pass


def IntegerField(default: int = 0, unique: bool = False, null: bool = None) -> Any:
    pass


class IntegrityError(Exception):
    pass


JOIN: Any = None
fn: Any = None

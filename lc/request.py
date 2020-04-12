import abc
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from typing import List, Mapping, Optional, TypeVar, Type

import lc.config as c

T = TypeVar("T")


class Request(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def from_form(cls: Type[T], form: Mapping[str, str]) -> T:
        pass

    # technically this gets added by dataclass_json, but mypy isn't
    # aware of it, so it's going to get declared here as though it
    # weren't abstract and then dataclass_json will add it
    @classmethod
    def from_json(cls: Type[T], json: bytes) -> T:
        pass


@dataclass_json
@dataclass
class User(Request):
    name: str
    password: str

    @classmethod
    def from_form(cls, form: Mapping[str, str]):
        return cls(name=form["username"], password=form["password"],)

    def to_token(self) -> str:
        return c.serializer.dumps({"name": self.name, "password": self.password,})


@dataclass_json
@dataclass
class Link(Request):
    url: str
    name: str
    description: str
    private: bool
    tags: List[str]
    created: Optional[datetime] = None

    @classmethod
    def from_form(cls, form: Mapping[str, str]):
        return cls(
            url=form["url"],
            name=form["name"],
            description=form["description"],
            private="private" in form,
            tags=form["tags"].split(),
        )

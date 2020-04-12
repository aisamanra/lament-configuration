import abc
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from typing import List, Mapping, Optional

import lc.config as c


class Request(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def from_form(cls, form: Mapping[str, str]):
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
        return c.SERIALIZER.dumps({"name": self.name, "password": self.password,})


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

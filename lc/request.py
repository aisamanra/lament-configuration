from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List


@dataclass_json
@dataclass
class User:
    name: str
    password: str

    @classmethod
    def from_form(cls, form):
        return cls(name=form["username"], password=form["password"],)


@dataclass_json
@dataclass
class Link:
    url: str
    name: str
    description: str
    private: bool
    tags: List[str]

    @classmethod
    def from_form(cls, form):
        return cls(
            url=form["url"],
            name=form["name"],
            description=form["description"],
            private="private" in form,
            tags=form["tags"].split(),
        )

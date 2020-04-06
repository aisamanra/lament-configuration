from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List


@dataclass_json
@dataclass
class User:
    name: str


@dataclass_json
@dataclass
class Link:
    url: str
    name: str
    description: str
    private: bool
    tags: List[str]

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, List

import lc.config as c


class View:
    pass


@dataclass
class Pagination(View):
    current: int
    last: int

    def previous(self) -> Optional[dict]:
        if self.current > 1:
            return {"page": self.current - 1}
        return None

    def next(self) -> Optional[dict]:
        if self.current < self.last:
            return {"page": self.current + 1}
        return None

    @classmethod
    def from_total(cls, current, total) -> "Pagination":
        return cls(current=current, last=((total - 1) // c.per_page) + 1,)


@dataclass
class UserInvite(View):
    claimed: bool
    claimant: str
    token: str

@dataclass
class AdminPane(View):
    invites: List[UserInvite]


@dataclass
class Config(View):
    username: str
    admin_pane: Optional[AdminPane]


@dataclass
class Tag(View):
    url: str
    name: str


@dataclass
class Link(View):
    id: int
    url: str
    name: str
    description: str
    private: bool
    tags: List[Tag]
    created: datetime
    is_mine: bool
    link_url: str


@dataclass
class LinkList(View):
    links: List[Any]
    pages: Optional[Pagination] = None


@dataclass
class SingleLink(View):
    link: Any


@dataclass
class Message(View):
    title: str
    message: str


@dataclass
class Page(View):
    title: str
    content: str
    user: Optional[Any]

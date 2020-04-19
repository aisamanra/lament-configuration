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
    msg: Optional[int] = None

    def bookmarklet_link(self):
        return (
            "javascript:(function(){window.open(`"
            + c.app_path
            + "/u/"
            + self.username
            + "/l?name=${document.title}&url=${document.URL}`);})();"
        )

    def message(self) -> Optional[str]:
        if self.msg == 1:
            return "Password changed."
        elif self.msg == 2:
            return "Mismatched new passwords; please try again."
        elif self.msg == 3:
            return "Incorrect old password; please try again."
        return None


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
    tags: List[Tag]
    pages: Optional[Pagination] = None


@dataclass
class SingleLink(View):
    link: Any


@dataclass
class Message(View):
    title: str
    message: str


@dataclass
class AddLinkDefaults(View):
    url: Optional[str] = None
    name: Optional[str] = None


@dataclass
class Page(View):
    title: str
    content: str
    user: Optional[Any]


@dataclass
class Error(View):
    code: int
    message: str

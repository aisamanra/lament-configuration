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
        return cls(current=current, last=((total - 1) // c.app.per_page) + 1,)


@dataclass
class UserInvite(View):
    claimed: bool
    claimant: str
    token: str


@dataclass
class AddUser(View):
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
            + c.app.config.app_path
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
class HierTagList:
    user: str
    tags: List[Tag]

    def render(self) -> str:
        groups: dict = {}

        for tag in (t.name for t in self.tags):
            if "/" not in tag:
                groups[tag] = groups.get(tag, {})
            else:
                chunks = tag.split("/")
                focus = groups[chunks[0]] = groups.get(chunks[0], {})
                for c in chunks[1:]:
                    focus[c] = focus = focus.get(c, {})

        return "\n".join(self.render_html(k, v) for k, v in groups.items())

    def render_html(self, prefix: str, values: dict) -> str:
        link = self._render_html(prefix, values, [])
        return f'<span class="tag">{link}</span>'

    def _href(self, tag: str, init: List[str]) -> str:
        link = "/".join(init + [tag])
        return f'<a href="/u/{self.user}/t/{link}">{tag}</a>'

    def _render_html(self, prefix: str, values: dict, init: List[str]) -> str:
        if not values:
            return self._href(prefix, init)
        if len(values) == 1:
            k, v = values.popitem()
            rest = self._render_html(k, v, init + [prefix])
            prefix_href = self._href(prefix, init)
            return f"{prefix_href}/{rest}"
        else:
            fragments = []
            for k, v in values.items():
                fragments.append(self._render_html(k, v, init + [prefix]))
            items = ", ".join(fragments)
            prefix_href = self._href(prefix, init)
            return f"{prefix_href}/{{{items}}}"


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

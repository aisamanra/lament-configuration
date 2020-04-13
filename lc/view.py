from dataclasses import dataclass
from typing import Optional, List

class View: pass

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
class Page(View):
    title: str
    content: str
    user: Optional[str]

from dataclasses import dataclass
import datetime
from passlib.apps import custom_app_context as pwd
import peewee
import playhouse.shortcuts
from typing import List, Optional, Tuple

import lc.config as c
import lc.error as e
import lc.request as r


class Model(peewee.Model):
    class Meta:
        database = c.db

    def to_dict(self) -> dict:
        return playhouse.shortcuts.model_to_dict(self)


@dataclass
class Pagination:
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


class User(Model):
    """
    A user! you know tf this is about
    """

    name = peewee.TextField(unique=True)
    passhash = peewee.TextField()
    is_admin = peewee.BooleanField(default=False)

    @staticmethod
    def from_request(user: r.User) -> "User":
        passhash = pwd.hash(user.password)
        try:
            return User.create(name=user.name, passhash=passhash,)
        except peewee.IntegrityError:
            raise e.UserExists(name=user.name)

    @staticmethod
    def from_invite(user: r.User, token: str) -> "User":
        invite = UserInvite.by_code(token)
        if invite.claimed_by is not None or invite.claimed_at is not None:
            raise e.AlreadyUsedInvite(invite=token)
        u = User.from_request(user)
        invite.claimed_at = datetime.datetime.now()
        invite.claimed_by = u
        invite.save()
        return u

    def authenticate(self, password: str) -> bool:
        return pwd.verify(password, self.passhash)

    def set_as_admin(self):
        self.is_admin = True
        self.save()

    @staticmethod
    def login(user: r.User) -> Tuple["User", str]:
        u = User.by_slug(user.name)
        if not u.authenticate(user.password):
            raise e.BadPassword(name=user.name)
        return u, user.to_token()

    @staticmethod
    def by_slug(slug: str) -> "User":
        u = User.get_or_none(name=slug)
        if u is None:
            raise e.NoSuchUser(name=slug)
        return u

    def base_url(self) -> str:
        return f"/u/{self.name}"

    def get_links(self, as_user: r.User, page: int) -> Tuple[List["Link"], Pagination]:
        links = (
            Link.select()
            .where((Link.user == self) & ((self == as_user) | (Link.private == False)))
            .order_by(-Link.created)
            .paginate(page, c.per_page)
        )
        pagination = Pagination.from_total(page, Link.select().count())
        return links, pagination

    def get_link(self, link_id: int) -> "Link":
        return Link.get((Link.user == self) & (Link.id == link_id))

    def get_tag(self, tag_name: str) -> "Tag":
        return Tag.get((Tag.user == self) & (Tag.name == tag_name))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    def get_config(self) -> dict:
        admin_pane = None
        if self.is_admin:
            user_invites = [
                {
                    "claimed": ui.claimed_by is not None,
                    "claimant": ui.claimed_by and ui.claimed_by.name,
                    "token": ui.token,
                }
                for ui in UserInvite.select().where(UserInvite.created_by == self)
            ]
            admin_pane = {"invites": user_invites}
        return {
            "username": self.name,
            "admin_pane": admin_pane,
        }


class Link(Model):
    """
    A link as stored in the database
    """

    url = peewee.TextField()
    name = peewee.TextField()
    description = peewee.TextField()
    # TODO: do we need to track modified time?
    created = peewee.DateTimeField()
    # is the field entirely private?
    private = peewee.BooleanField()
    # owned by
    user = peewee.ForeignKeyField(User, backref="links")

    def link_url(self) -> str:
        return f"/u/{self.user.name}/l/{self.id}"

    @staticmethod
    def by_id(id: int) -> Optional["Link"]:
        return Link.get_or_none(id=id)


    @staticmethod
    def from_request(user: User, link: r.Link) -> "Link":
        l = Link.create(
            url=link.url,
            name=link.name,
            description=link.description,
            private=link.private,
            created=link.created or datetime.datetime.now(),
            user=user,
        )
        for tag_name in link.tags:
            t = Tag.get_or_create_tag(user, tag_name)
            HasTag.create(
                link=l, tag=t,
            )
        return l

    def update_from_request(self, user: User, link: r.Link):

        req_tags = set(link.tags)

        for hastag in self.tags:
            name = hastag.tag.name
            if name not in req_tags:
                hastag.delete_instance()
            else:
                req_tags.remove(name)

        for tag_name in req_tags:
            t = Tag.get_or_create_tag(user, tag_name)
            HasTag.get_or_create(link=self, tag=t)

        self.url = link.url
        self.name = link.name
        self.description = link.description
        self.private = link.private
        self.save()


class Tag(Model):
    """
    A tag. This just indicates that a user has used this tag at some point.
    """

    name = peewee.TextField()
    parent = peewee.ForeignKeyField("self", null=True, backref="children")
    user = peewee.ForeignKeyField(User, backref="tags")

    def url(self) -> str:
        return f"/u/{self.user.name}/t/{self.name}"

    def get_links(self, as_user: r.User, page: int) -> Tuple[List[Link], Pagination]:
        links = [
            ht.link
            for ht in HasTag.select()
            .join(Link)
            .where(
                (HasTag.tag == self)
                & ((HasTag.link.user == as_user) | (HasTag.link.private == False))
            )
            .order_by(-Link.created)
            .paginate(page, c.per_page)
        ]
        pagination = Pagination.from_total(
            page, HasTag.select().where((HasTag.tag == self)).count(),
        )
        return links, pagination

    @staticmethod
    def get_or_create_tag(user: User, tag_name: str):
        if (t := Tag.get_or_none(name=tag_name, user=user)) :
            return t

        parent = None
        if "/" in tag_name:
            parent_name = tag_name[: tag_name.rindex("/")]
            parent = Tag.get_or_create_tag(user, parent_name)

        return Tag.create(name=tag_name, parent=parent, user=user)


class HasTag(Model):
    """
    Establishes that a link is tagged with a given tag.
    """

    link = peewee.ForeignKeyField(Link, backref="tags")
    tag = peewee.ForeignKeyField(Tag, backref="models")

    @staticmethod
    def get_or_create(link: Link, tag: Tag):
        res = HasTag.get_or_none(link=link, tag=tag)
        if res is None:
            res = HasTag.create(link=link, tag=tag)

        return res


class UserInvite(Model):
    token = peewee.TextField(unique=True)

    created_by = peewee.ForeignKeyField(User, backref="invites")
    created_at = peewee.DateTimeField()

    claimed_by = peewee.ForeignKeyField(User, null=True)
    claimed_at = peewee.DateTimeField(null=True)

    @staticmethod
    def by_code(token: str) -> "UserInvite":
        if (u := UserInvite.get_or_none(token=token)) :
            return u
        raise e.NoSuchInvite(invite=token)

    @staticmethod
    def manufacture(creator: User) -> "UserInvite":
        now = datetime.datetime.now()
        token = c.serializer.dumps(
            {"created_at": now.timestamp(), "created_by": creator.name,}
        )
        return UserInvite.create(
            token=token,
            created_by=creator,
            created_at=now,
            claimed_by=None,
            claimed_at=None,
        )


MODELS = [
    User,
    Link,
    Tag,
    HasTag,
    UserInvite,
]


def create_tables():
    c.db.create_tables(MODELS, safe=True)

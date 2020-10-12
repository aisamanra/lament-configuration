from contextlib import contextmanager
import datetime
import json
from passlib.apps import custom_app_context as pwd
import peewee
import playhouse.shortcuts
from typing import Iterator, List, Optional, Tuple

import lc.config as c
import lc.error as e
import lc.request as r
import lc.view as v


class Model(peewee.Model):
    class Meta:
        database = c.app.db

    def to_dict(self) -> dict:
        return playhouse.shortcuts.model_to_dict(self)

    @contextmanager
    def atomic(self):
        with c.app.db.atomic():
            yield


class Meta(Model):

    version = peewee.IntegerField(default=0)

    @staticmethod
    def fetch():
        try:
            return Meta.get(id=0)
        except Exception:
            meta = Meta.create(id=0)
            return meta


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
            return User.create(
                name=user.name,
                passhash=passhash,
            )
        except peewee.IntegrityError:
            raise e.UserExists(name=user.name)

    def change_password(self, req: r.PasswordChange):
        if not pwd.verify(req.old, self.passhash):
            raise e.BadPassword(name=self.name)
        self.passhash = pwd.hash(req.n1)
        self.save()

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

    def config_url(self) -> str:
        return f"/u/{self.name}/config"

    def get_links(
        self, as_user: Optional["User"], page: int
    ) -> Tuple[List[v.Link], v.Pagination]:
        query = Link.select().where(
            (Link.user == self)
            & ((self == as_user) | (Link.private == False))  # noqa: E712
        )
        links = query.order_by(-Link.created).paginate(page, c.app.per_page)
        link_views = [link.to_view(as_user) for link in links]
        pagination = v.Pagination.from_total(page, query.count())
        return link_views, pagination

    def get_link(self, link_id: int) -> "Link":
        try:
            return Link.get((Link.user == self) & (Link.id == link_id))
        except Link.DoesNotExist:
            raise e.NoSuchLink(link_id)

    def get_tag(self, tag_name: str) -> "Tag":
        return Tag.get((Tag.user == self) & (Tag.name == tag_name))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    def get_config(self, status_msg: Optional[int]) -> v.Config:
        admin_pane = None
        if self.is_admin:
            user_invites = [
                v.UserInvite(
                    claimed=ui.claimed_by is not None,
                    claimant=ui.claimed_by and ui.claimed_by.name,
                    token=ui.token,
                )
                for ui in UserInvite.select().where(UserInvite.created_by == self)
            ]
            admin_pane = v.AdminPane(invites=user_invites)
        return v.Config(username=self.name, admin_pane=admin_pane, msg=status_msg)

    def import_pinboard_data(self, stream):
        try:
            links = json.load(stream)
        except json.decoder.JSONDecodeError:
            raise e.BadFileUpload("could not parse file as JSON")

        if not isinstance(links, list):
            raise e.BadFileUpload("expected a list")

        # create and (for this session) cache the tags
        tags = {}
        for link in links:
            if "tags" not in link:
                raise e.BadFileUpload("missing key {exn.args[0]}")
            for t in link["tags"].split():
                if t in tags:
                    continue

                tags[t] = Tag.get_or_create_tag(self, t)

        with self.atomic():
            for link in links:
                try:
                    time = datetime.datetime.strptime(
                        link["time"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    ln = Link.create(
                        url=link["href"],
                        name=link["description"],
                        description=link["extended"],
                        private=link["shared"] == "no",
                        created=time,
                        user=self,
                    )
                except KeyError as exn:
                    raise e.BadFileUpload(f"missing key {exn.args[0]}")
                for t in link["tags"].split():
                    HasTag.get_or_create(link=ln, tag=tags[t])

    def get_tags(self) -> List[v.Tag]:
        return sorted(
            (t.to_view() for t in self.tags),  # type: ignore
            key=lambda t: t.name,
        )

    def get_related_tags(self, tag: "Tag") -> List[v.Tag]:
        # SELECT * from has_tag t1, has_tag t2, link l
        #   WHERE t1.link_id == l.id AND t2.link_id == l.id
        #   AND t1.id != t2.id AND t1 = self
        SelfTag = HasTag.alias()
        query = (
            HasTag.select(HasTag.tag)
            .join(Link, on=(HasTag.link == Link.id))
            .join(SelfTag, on=(SelfTag.link == Link.id))
            .where((SelfTag.tag == tag) & (SelfTag.id != HasTag.id))
            .group_by(HasTag.tag)
        )
        return sorted(
            (t.tag.to_view() for t in query),
            key=lambda t: t.name,
        )

    def get_string_search(
        self, needle: str, as_user: Optional["User"], page: int
    ) -> Tuple[List[v.Link], v.Pagination]:
        """
        Find all links that contain the string `needle` somewhere in their URL or title
        """
        query = Link.select().where(
            (Link.user == self)
            & ((self == as_user) | (Link.private == False))  # noqa: E712
            & (Link.name.contains(needle) | Link.description.contains(needle))
        )
        links = query.order_by(-Link.created).paginate(page, c.app.per_page)
        link_views = [link.to_view(as_user) for link in links]
        pagination = v.Pagination.from_total(page, query.count())
        return link_views, pagination


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
    def get_all(
        as_user: Optional[User], page: int
    ) -> Tuple[List["Link"], v.Pagination]:
        links = (
            Link.select()
            .where((Link.user == as_user) | (Link.private == False))  # noqa: E712
            .order_by(-Link.created)
            .paginate(page, c.app.per_page)
        )
        link_views = [link.to_view(as_user) for link in links]
        pagination = v.Pagination.from_total(page, Link.select().count())
        return link_views, pagination

    @staticmethod
    def from_request(user: User, link: r.Link) -> "Link":
        new_link = Link.create(
            url=link.url,
            name=link.name,
            description=link.description,
            private=link.private,
            created=link.created or datetime.datetime.now(),
            user=user,
        )
        for tag_name in link.tags:
            tag = Tag.get_or_create_tag(user, tag_name)
            HasTag.get_or_create(link=new_link, tag=tag)
        return new_link

    def update_from_request(self, user: User, link: r.Link):
        with self.atomic():
            req_tags = set(link.tags)

            for hastag in self.tags:  # type: ignore
                name = hastag.tag.name
                if name not in req_tags:
                    hastag.delete_instance()
                else:
                    req_tags.remove(name)

            for tag_name in req_tags:
                t = Tag.get_or_create_tag(user, tag_name)
                HasTag.get_or_create(link=self, tag=t)

            Tag.clean()

            self.url = link.url
            self.name = link.name
            self.description = link.description
            self.private = link.private
            self.save()

    def to_view(self, as_user: Optional[User]) -> v.Link:
        return v.Link(
            id=self.id,
            url=self.url,
            name=self.name,
            description=self.description,
            private=self.private,
            tags=self.get_tags_view(),
            created=self.created,
            is_mine=self.user.id == as_user.id if as_user else False,
            link_url=self.link_url(),
            user=self.user.name,
        )

    def get_tags_view(self) -> List[v.Tag]:
        return [
            v.Tag(url=f"/u/{self.user.name}/t/{ht.tag.name}", name=ht.tag.name)
            for ht in HasTag().select(Tag.name).join(Tag).where(HasTag.link == self)
        ]


class Tag(Model):
    """
    A tag. This just indicates that a user has used this tag at some point.
    """

    name = peewee.TextField()
    parent = peewee.ForeignKeyField("self", null=True, backref="children")
    user = peewee.ForeignKeyField(User, backref="tags")

    def url(self) -> str:
        return f"/u/{self.user.name}/t/{self.name}"

    def get_links(
        self, as_user: Optional[User], page: int
    ) -> Tuple[List[Link], v.Pagination]:
        query = (
            HasTag.select()
            .join(Link)
            .where(
                (HasTag.tag == self)
                & (
                    (HasTag.link.user == as_user)
                    | (HasTag.link.private == False)  # noqa: E712
                )
            )
        )
        links = [
            ht.link.to_view(as_user)
            for ht in query.order_by(-Link.created).paginate(page, c.app.per_page)
        ]
        pagination = v.Pagination.from_total(page, query.count())
        return links, pagination

    def get_family(self) -> Iterator["Tag"]:
        yield self
        p = self
        while p := p.parent:
            yield p

    BAD_TAG_CHARS = set("{}\\#")

    @staticmethod
    def is_valid_tag_name(tag_name: str) -> bool:
        return all((c not in Tag.BAD_TAG_CHARS for c in tag_name))

    @staticmethod
    def get_or_create_tag(user: User, tag_name: str) -> "Tag":
        if t := Tag.get_or_none(name=tag_name, user=user):
            return t

        if not Tag.is_valid_tag_name(tag_name):
            raise e.BadTagName(tag_name)

        parent = None
        if "/" in tag_name:
            parent_name = tag_name[: tag_name.rindex("/")]
            parent = Tag.get_or_create_tag(user, parent_name)

        return Tag.create(name=tag_name, parent=parent, user=user)

    def to_view(self) -> v.Tag:
        return v.Tag(url=self.url(), name=self.name)

    @staticmethod
    def clean():
        unused = (
            Tag.select(Tag.id)  # type: ignore
            .join(HasTag, peewee.JOIN.LEFT_OUTER)
            .group_by(Tag.name)
            .having(peewee.fn.COUNT(HasTag.id) == 0)
        )
        Tag.delete().where(Tag.id.in_(unused)).execute()  # type: ignore


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

        if tag.parent:
            HasTag.get_or_create(link, tag.parent)

        return res


class UserInvite(Model):
    token = peewee.TextField(unique=True)

    created_by = peewee.ForeignKeyField(User, backref="invites")
    created_at = peewee.DateTimeField()

    claimed_by = peewee.ForeignKeyField(User, null=True)
    claimed_at = peewee.DateTimeField(null=True)

    @staticmethod
    def by_code(token: str) -> "UserInvite":
        if u := UserInvite.get_or_none(token=token):
            return u
        raise e.NoSuchInvite(invite=token)

    @staticmethod
    def manufacture(creator: User) -> "UserInvite":
        now = datetime.datetime.now()
        token = c.app.serialize_token(
            {
                "created_at": now.timestamp(),
                "created_by": creator.name,
            }
        )
        return UserInvite.create(
            token=token,
            created_by=creator,
            created_at=now,
            claimed_by=None,
            claimed_at=None,
        )


MODELS = [
    Meta,
    User,
    Link,
    Tag,
    HasTag,
    UserInvite,
]


def create_tables():
    c.app.db.create_tables(MODELS, safe=True)

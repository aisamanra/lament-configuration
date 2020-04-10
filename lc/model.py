import datetime
from passlib.apps import custom_app_context as pwd
import peewee
import playhouse.shortcuts
import typing

import lc.config as c
import lc.error as e
import lc.request as r


class Model(peewee.Model):
    class Meta:
        database = c.DB

    def to_dict(self) -> dict:
        return playhouse.shortcuts.model_to_dict(self)


# TODO: figure out authorization for users (oauth? passwd?)
class User(Model):
    """
    A user! you know tf this is about
    """

    name = peewee.TextField(unique=True)
    passhash = peewee.TextField()

    @staticmethod
    def from_request(user: r.User) -> "User":
        passhash = pwd.hash(user.password)
        try:
            return User.create(name=user.name, passhash=passhash,)
        except peewee.IntegrityError:
            raise e.UserExists(name=user.name)

    def authenticate(self, password: str) -> bool:
        return pwd.verify(password, self.passhash)

    @staticmethod
    def login(user: r.User) -> "User":
        u = User.by_slug(user.name)
        if not u.authenticate(user.password):
            raise e.BadPassword(name=user.name)
        return c.SERIALIZER.dumps(user.to_dict())

    @staticmethod
    def by_slug(slug: str) -> "User":
        u = User.get_or_none(name=slug)
        if u is None:
            raise e.NoSuchUser(name=slug)
        return u

    def base_url(self) -> str:
        return f"/u/{self.name}"

    def get_links(self, page: int) -> typing.List["Link"]:
        return Link.select().where(Link.user == self).paginate(page, c.PER_PAGE)

    def get_tag(self, tag_name: str) -> "Tag":
        return Tag.get((Tag.user == self) & (Tag.name == tag_name))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


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
    def from_request(user: User, link: r.Link) -> "Link":
        l = Link.create(
            url=link.url,
            name=link.name,
            description=link.description,
            private=link.private,
            created=datetime.datetime.now(),
            user=user,
        )
        for tag_name in link.tags:
            t = Tag.get_or_create_tag(user, tag_name)
            HasTag.create(
                link=l, tag=t,
            )
        return l


class Tag(Model):
    """
    A tag. This just indicates that a user has used this tag at some point.
    """

    name = peewee.TextField()
    parent = peewee.ForeignKeyField("self", null=True, backref="children")
    user = peewee.ForeignKeyField(User, backref="tags")

    def url(self) -> str:
        return f"/u/{self.user.name}/t/{self.name}"

    def get_links(self, page: int) -> typing.List[Link]:
        return [
            ht.link
            for ht in HasTag.select()
            .where((HasTag.tag == self))
            .paginate(page, c.PER_PAGE)
        ]

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


MODELS = [
    User,
    Link,
    Tag,
    HasTag,
]


def create_tables():
    c.DB.create_tables(MODELS, safe=True)

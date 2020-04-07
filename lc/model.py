import datetime
import peewee

import lc.config
import lc.request as r


class Model(peewee.Model):
    class Meta:
        database = lc.config.DB


# TODO: figure out authorization for users (oauth? passwd?)
class User(Model):
    """
    A user! you know tf this is about
    """

    name = peewee.TextField()

    @staticmethod
    def from_request(user: r.User) -> "User":
        return User.create(name=user.name)

    @staticmethod
    def by_slug(slug: str) -> "User":
        return User.get(name=slug)

    def base_url(self) -> str:
        return f"/u/{self.name}"


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
            t = Tag.find_tag(user, tag_name)
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

    @staticmethod
    def find_tag(user: User, tag_name: str):
        if (t := Tag.get_or_none(name=tag_name, user=user)) :
            return t

        parent = None
        if "/" in tag_name:
            parent_name = tag_name[: tag_name.rindex("/")]
            parent = Tag.find_tag(user, parent_name)

        return Tag.create(name=tag_name, parent=parent, user=user,)


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
    lc.config.DB.create_tables(MODELS, safe=True)

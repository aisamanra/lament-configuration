import peewee

import lc.config

class Model(peewee.Model):
    class Meta:
        database = lc.config.DB

# TODO: figure out authorization for users (oauth? passwd?)
class User(Model):
    '''
    A user! you know tf this is about
    '''
    name = peewee.TextField()


class Link(Model):
    '''
    A link as stored in the database
    '''

    url = peewee.TextField()
    name = peewee.TextField()
    description = peewee.TextField()
    # TODO: do we need to track modified time?
    created = peewee.DateTimeField()
    # is the field entirely private?
    private = peewee.BooleanField()


class Tag(Model):
    '''
    A tag. This just indicates that a user has used this tag at some point.
    '''
    name = peewee.TextField()
    parent = peewee.ForeignKeyField('self', null=True, backref='children')


class HasTag(Model):
    '''
    Establishes that a link is tagged with a given tag.
    '''
    link = peewee.ForeignKeyField(Link, backref='tags')
    tag = peewee.ForeignKeyField(Tag, backref='models')


MODELS = [
    User,
    Link,
    Tag,
    HasTag,
]

def create_tables():
    lc.config.DB.create_tables(MODELS, safe=True)

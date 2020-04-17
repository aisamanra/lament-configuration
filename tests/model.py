import peewee
import pytest

import lc.config as c
import lc.error as e
import lc.request as r
import lc.model as m


class Testdb:
    def setup_method(self, _):
        c.db.init(":memory:")
        c.db.create_tables(m.MODELS)

    def teardown_method(self, _):
        c.db.close()

    def mk_user(self, name="gdritter", password="foo") -> m.User:
        return m.User.from_request(r.User(name=name, password=password,))

    def test_create_user(self):
        name = "gdritter"
        u = self.mk_user(name=name)

        # it should be the only thing in the db
        all_users = m.User.select()
        assert len(all_users) == 1
        assert all_users[0].id == u.id
        assert all_users[0].name == name

        # we should be able to find it with the given name, too
        named_user = m.User.get(m.User.name == name)
        assert named_user.id == u.id
        assert named_user.name == name

    def test_user_passwords(self):
        name = "gdritter"
        password = "foo"

        u = self.mk_user(name=name, password=password)
        print(u.name, u.passhash)

        assert u.authenticate(password)
        assert u.authenticate("wrong password") is False

    def test_no_duplicate_users(self):
        name = "gdritter"
        u1 = self.mk_user(name=name)
        with pytest.raises(e.UserExists):
            u2 = self.mk_user(name=name)

    def test_get_or_create_tag(self):
        u = self.mk_user()

        tag_name = "food"
        t = m.Tag.get_or_create_tag(u, tag_name)

        # we should be able to find the tag with the given name
        named_tags = m.Tag.select(m.Tag.user == u and m.Tag.name == tag_name)
        assert len(named_tags) == 1

        # subsequent calls to get_or_create_tag should return the same db row
        t2 = m.Tag.get_or_create_tag(u, tag_name)
        assert t.id == t2.id

    def test_find_hierarchy(self):
        u = self.mk_user()
        t = m.Tag.get_or_create_tag(u, "food/bread/rye")

        # this should have created three db rows: for 'food', for
        # 'food/bread', and for 'food/bread/rye':
        assert len(m.Tag.select()) == 3

        # searching for a prefix of the tag should yield the same
        # parent tag
        assert t.parent.id == m.Tag.get(name="food/bread").id
        assert t.parent.parent.id == m.Tag.get(name="food").id

        # creating a new hierarchical tag with a shared prefix should
        # only create the new child tag
        t2 = m.Tag.get_or_create_tag(u, "food/bread/baguette")
        print([t.name for t in m.Tag.select()])

        assert len(m.Tag.select()) == 4
        # it should share the same parent tags
        assert t2.parent.id == t.parent.id
        assert t2.parent.parent.id == t.parent.parent.id

        # trying to get a hierarchical tag should result in the same
        # one already entered
        assert t.id == m.Tag.get(name="food/bread/rye").id
        assert t2.id == m.Tag.get(name="food/bread/baguette").id

    def test_create_invite(self):
        u = self.mk_user()
        invite = m.UserInvite.manufacture(u)

        # the invite should reference the user and be unclaimed
        assert invite.created_by.id == u.id
        assert invite.created_at is not None
        assert invite.claimed_by is None
        assert invite.claimed_at is None

        # deserializing the unique token should reveal the encrypted data
        raw_data = c.serializer.loads(invite.token)
        assert raw_data["created_by"] == u.name

    def test_use_invite(self):
        u = self.mk_user()
        initial_invite = m.UserInvite.manufacture(u)

        assert initial_invite.claimed_by is None
        assert initial_invite.claimed_at is None

        u2 = m.User.from_invite(r.User(name="u2", password="u2"), initial_invite.token)

        invite = m.UserInvite.by_code(initial_invite.token)
        assert invite.token == initial_invite.token
        assert invite.created_by.id == u.id
        assert invite.claimed_by.id == u2.id
        assert invite.created_at is not None
        assert invite.claimed_at is not None

    def bad_use_invite(self):
        initial_invite = m.UserInvite.manufacture(self.mk_user())

        # creating this user claims the invite
        m.User.from_invite(r.User(name="u2", password="u2"), initial_invite.token)

        # using the invite again raise an error
        with pytest.raises(e.AlreadyUsedInvite):
            m.User.from_invite(r.User(name="u3", password="u3"), initial_invite.token)

        with pytest.raises(e.NoSuchInvite):
            m.User.from_invite(r.User(name="u4", password="u4"), "a-non-existent-token")

    def check_tags(self, l, tags):
        present = set(map(lambda hastag: hastag.tag.name, l.tags))
        assert present == set(tags)

    def test_edit_link(self):
        u = self.mk_user()

        req = r.Link("http://foo.com", "foo", "", False, ["foo", "bar"])
        l = m.Link.from_request(u, req)
        assert l.name == req.name
        assert l.tags == ["foo", "bar"] # type: ignore

        # check the in-place update
        req.name = "bar"
        req.tags = ["bar", "baz"]
        req.private = True
        l.update_from_request(u, req)
        assert l.name == req.name
        assert l.private
        assert l.created != req.created
        self.check_tags(l, req.tags)

        # check that the link was persisted
        l2 = m.Link.by_id(l.id)
        assert l2
        assert l2.name == req.name
        assert l2.private
        assert l2.created != req.created
        self.check_tags(l2, req.tags)

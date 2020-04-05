import lc.config as c
import lc.model as m
import tempfile

class TestDB:
    def setup_method(self, _):
        c.DB.init(':memory:')
        c.DB.create_tables(m.MODELS)

    def test_create_user(self):
        name = 'gdritter'
        u = m.User.create(name=name)

        # it should be the only thing in the db
        all_users = m.User.select()
        assert len(all_users) == 1
        assert(all_users[0].id == u.id)
        assert(all_users[0].name == name)

        # we should be able to find it with the given name, too
        named_user = m.User.get(m.User.name == name)
        assert named_user.id == u.id
        assert named_user.name == name

    def test_find_tag(self):
        tag_name = 'food'
        t = m.Tag.find_tag(tag_name)

        # we should be able to find the tag with the given name
        named_tags = m.Tag.select(m.Tag.name == tag_name)
        assert len(named_tags) == 1

        # subsequent calls to find_tag should return the same db row
        t2 = m.Tag.find_tag(tag_name)
        assert t.id == t2.id

    def test_find_hierarchy(self):
        tag_name = 'food/bread/rye'
        t = m.Tag.find_tag(tag_name)

        # this should have created three DB rows: for 'food', for
        # 'food/bread', and for 'food/bread/rye':
        assert len(m.Tag.select()) == 3

        # searching for a prefix of the tag should yield the same
        # parent tag
        assert t.parent.id == m.Tag.get(name='food/bread').id
        assert t.parent.parent.id == m.Tag.get(name='food').id

        # creating a new hierarchical tag with a shared prefix should
        # only create the new child tag
        t2 = m.Tag.find_tag('food/bread/baguette')
        assert len(m.Tag.select()) == 4
        # it should share the same parent tags
        assert t2.parent.id == t.parent.id
        assert t2.parent.parent.id == t.parent.parent.id

        # trying to get a hierarchical tag should result in the same
        # one already entered
        assert t.id == m.Tag.get(name='food/bread/rye').id
        assert t2.id == m.Tag.get(name='food/bread/baguette').id


    def teardown_method(self, _):
        c.DB.close()

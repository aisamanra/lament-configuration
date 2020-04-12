import lc.config as c
import lc.model as m
import lc.app as a


class TestRoutes:
    def setup_method(self, _):
        c.db.init(":memory:")
        c.db.create_tables(m.MODELS)
        self.app = a.app.test_client()

    def teardown_method(self, _):
        c.db.close()

    def get(self, path):
        return self.app.get(path)

    def test_index(self):
        result = self.get("/")
        assert result.status == "200 OK"

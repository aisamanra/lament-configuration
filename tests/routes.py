import lc.config as c
import lc.model as m
import lc.routes as r


class TestRoutes:
    def setup_method(self, _):
        c.DB.init(":memory:")
        c.DB.create_tables(m.MODELS)
        self.app = r.app.test_client()

    def teardown_method(self, _):
        c.DB.close()

    def get(self, path):
        return self.app.get(path)

    def test_index(self):
        result = self.get("/")
        assert result.status == "200 OK"

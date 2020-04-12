import json

import lc.config as c
import lc.model as m
import lc.request as r
import lc.app as a


class TestRoutes:
    def setup_method(self, _):
        c.db.init(":memory:")
        c.db.create_tables(m.MODELS)
        self.app = a.app.test_client()

    def teardown_method(self, _):
        c.db.close()

    def mk_user(self, name="gdritter", password="foo") -> m.User:
        return m.User.from_request(r.User(name=name, password=password,))

    def test_index(self):
        result = self.app.get("/")
        assert result.status == "200 OK"

    def test_successful_api_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(password=password)
        result = self.app.post("/auth", json={"name": username, "password": password,})
        assert result.status == "200 OK"
        decoded_token = c.serializer.loads(result.json["token"])
        assert decoded_token["name"] == username
        assert decoded_token["password"] == password

    def test_failed_api_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(password=password)
        result = self.app.post("/auth", json={"name": username, "password": "foo",})
        assert result.status == "403 FORBIDDEN"

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

    def mk_user(self, username="gdritter", password="foo") -> m.User:
        return m.User.from_request(r.User(name=username, password=password,))

    def test_index(self):
        result = self.app.get("/")
        assert result.status == "200 OK"

    def test_successful_api_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(username=username, password=password)
        result = self.app.post("/auth", json={"name": username, "password": password})
        assert result.status == "200 OK"
        decoded_token = c.serializer.loads(result.json["token"])
        assert decoded_token["name"] == username
        assert decoded_token["password"] == password

    def test_failed_api_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(username=username, password=password)
        result = self.app.post("/auth", json={"name": username, "password": "foo"})
        assert result.status == "403 FORBIDDEN"

    def test_successful_web_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(username=username, password=password)
        result = self.app.post(
            "/auth",
            data={"username": username, "password": password},
            follow_redirects=True,
        )
        assert result.status == "200 OK"

    def test_failed_web_login(self):
        username = "gdritter"
        password = "bar"
        u = self.mk_user(username=username, password=password)
        result = self.app.post("/auth", data={"username": username, "password": "foo"})
        assert result.status == "403 FORBIDDEN"

    def test_successful_api_add_link(self):
        password = "foo"
        u = self.mk_user(password=password)
        result = self.app.post("/auth", json={"name": u.name, "password": password})
        assert result.status == "200 OK"
        token = result.json["token"]
        result = self.app.post(
            f"/u/{u.name}/l",
            json={
                "url": "http://example.com/",
                "name": "Example Dot Com",
                "description": "Some Description",
                "private": False,
                "tags": ["website"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert result.status == "200 OK"
        assert result.json["url"] == "http://example.com/"

    def test_no_permissions_api_add_link(self):
        # create a user who owns a link collection
        owner = self.mk_user()
        password = "foo"

        # and another user who should not be able to post to it
        interloper = self.mk_user(username="interloper", password=password)

        # authenticate as interloper
        result = self.app.post(
            "/auth", json={"name": interloper.name, "password": password}
        )
        assert result.status == "200 OK"
        token = result.json["token"]

        # try to add a link to owner's collection
        result = self.app.post(
            f"/u/{owner.name}/l",
            json={
                "url": "http://example.com/",
                "name": "Example Dot Com",
                "description": "Some Description",
                "private": False,
                "tags": ["website"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert result.status == "403 FORBIDDEN"

import os
import json

os.environ["LC_DB_PATH"] = ":memory:"
os.environ["LC_SECRET_KEY"] = "TEST_KEY"
os.environ["LC_APP_PATH"] = "localhost"

import lc.config as c
import lc.model as m
import lc.request as r
import lc.app as a


class TestRoutes:
    def setup_method(self, _):
        c.app.in_memory_db()
        m.create_tables()
        self.app = a.app.test_client()

    def teardown_method(self, _):
        c.app.close_db()

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
        decoded_token = c.app.load_token(result.json["token"])
        assert decoded_token["name"] == username

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

    def test_successful_api_delete_link(self):
        password = "foo"
        u = self.mk_user(password=password)
        result = self.app.post("/auth", json={"name": u.name, "password": password})
        assert result.status == "200 OK"
        token = result.json["token"]

        sample_url = "http://example.com/"
        result = self.app.post(
            f"/u/{u.name}/l",
            json={
                "url": sample_url,
                "name": "Example Dot Com",
                "description": "Some Description",
                "private": False,
                "tags": ["website"],
            },
        )
        link_id = result.json["id"]

        # this should be fine
        check_link = self.app.get(
            f"/u/{u.name}/l/{link_id}", headers={"Content-Type": "application/json"},
        )
        assert check_link.status == "200 OK"
        assert check_link.json["url"] == sample_url

        # delete the link
        delete_link = self.app.delete(
            f"/u/{u.name}/l/{link_id}", headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_link.status == "200 OK"

        # make sure it is gone
        bad_result = self.app.get(
            f"/u/{u.name}/l/{link_id}", headers={"Content-Type": "application/json"},
        )
        assert bad_result.status == "404 NOT FOUND"

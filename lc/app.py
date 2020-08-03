import contextlib
import os
import flask
import sys

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r
import lc.view as v
from lc.web import Endpoint, endpoint, render

app = c.app.app


@endpoint("/")
class Index(Endpoint):
    def html(self):

        pg = int(flask.request.args.get("page", 1))
        links, pages = m.Link.get_all(as_user=self.user, page=pg)
        linklist = v.LinkList(links=links, pages=pages, user="", tags=[])

        return render(
            "main",
            v.Page(title="main", content=render("linklist", linklist), user=self.user,),
        )


@endpoint("/auth")
class Auth(Endpoint):
    def api_post(self):
        u, token = m.User.login(self.request_data(r.User))
        flask.session["auth"] = token
        return self.api_ok(u.base_url(), {"token": token})


@endpoint("/login")
class Login(Endpoint):
    def html(self):
        return render(
            "main", v.Page(title="login", content=render("login"), user=self.user,)
        )


@endpoint("/logout")
class Logout(Endpoint):
    def html(self):
        if "auth" in flask.session:
            del flask.session["auth"]
        raise e.LCRedirect("/")

    def api_post(self):
        if "auth" in flask.session:
            del flask.session["auth"]
        return self.api_ok("/")


@endpoint("/u")
class CreateUser(Endpoint):
    def html(self):
        if self.user:
            raise e.LCRedirect(f"/u/{self.user.name}")

        token = flask.request.args.get("token")
        if not token:
            raise e.LCRedirect("/")

        add_user = v.AddUser(token=token)
        return render(
            "main",
            v.Page(
                title="add user", user=self.user, content=render("add_user", add_user),
            ),
        )

    def api_post(self):
        token = flask.request.args["token"]
        req = self.request_data(r.NewUser).to_user_request()
        u = m.User.from_invite(req, token)
        flask.session["auth"] = req.to_token()
        return self.api_ok(u.base_url(), u.to_dict())


@endpoint("/u/<string:slug>")
class GetUser(Endpoint):
    def html(self, slug: str):
        u = m.User.by_slug(slug)
        pg = int(flask.request.args.get("page", 1))
        tags = u.get_tags()
        links, pages = u.get_links(as_user=self.user, page=pg)
        linklist = v.LinkList(links=links, user=slug, pages=pages, tags=tags)
        return render(
            "main",
            v.Page(
                title=f"user {u.name}",
                content=render("linklist", linklist),
                user=self.user,
            ),
        )

    def api_get(self, slug: str):
        return m.User.by_slug(slug).to_dict()


@endpoint("/u/<string:user>/config")
class GetUserConfig(Endpoint):
    def html(self, user: str):
        u = self.require_authentication(user)
        status_msg = flask.request.args.get("m", None)
        if status_msg is not None:
            status_msg = int(status_msg)
        return render(
            "main",
            v.Page(
                title="configuration",
                content=render("config", u.get_config(status_msg)),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/invite")
class CreateInvite(Endpoint):
    def api_post(self, user: str):
        u = self.require_authentication(user)
        invite = m.UserInvite.manufacture(u)
        return self.api_ok(f"/u/{user}/config", {"invite": invite.token})


@endpoint("/u/<string:user>/password")
class ChangePassword(Endpoint):
    def api_post(self, user: str):
        u = self.require_authentication(user)
        config_url = u.config_url()
        req = self.request_data(r.PasswordChange)
        try:
            req.require_match()
        except e.MismatchedPassword:
            raise e.LCRedirect(f"{config_url}?m=2")
        try:
            u.change_password(req)
        except e.BadPassword:
            raise e.LCRedirect(f"{config_url}?m=3")
        return self.api_ok(f"{config_url}?m=1")


@endpoint("/u/<string:user>/l")
class CreateLink(Endpoint):
    def html(self, user: str):
        u = self.require_authentication(user)
        url = flask.request.args.get("url", "")
        name = flask.request.args.get("name", "")
        tags = u.get_tags()
        defaults = v.AddLinkDefaults(user=user, name=name, url=url, all_tags=tags,)
        return render(
            "main",
            v.Page(
                title="login", content=render("add_link", defaults), user=self.user,
            ),
        )

    def api_post(self, user: str):
        u = self.require_authentication(user)
        req = self.request_data(r.Link)
        l = m.Link.from_request(u, req)
        return self.api_ok(l.link_url(), l.to_dict())


@endpoint("/u/<string:user>/l/<string:link>")
class GetLink(Endpoint):
    def api_get(self, user: str, link: str):
        u = self.require_authentication(user)
        l = u.get_link(int(link))
        return self.api_ok(l.link_url(), l.to_dict())

    def api_post(self, user: str, link: str):
        u = self.require_authentication(user)
        l = u.get_link(int(link))
        req = self.request_data(r.Link)
        l.update_from_request(u, req)
        raise e.LCRedirect(l.link_url())

    def api_delete(self, user: str, link: str):
        u = self.require_authentication(user)
        u.get_link(int(link)).delete_instance()
        return self.api_ok(u.base_url())

    def html(self, user: str, link: str):
        l = m.User.by_slug(user).get_link(int(link))
        return render(
            "main",
            v.Page(
                title=f"link {l.name}",
                content=render(
                    "linklist", v.LinkList([l.to_view(self.user)], [], user=user)
                ),
                user=self.user,
            ),
        )


@endpoint("/u/<string:slug>/l/<string:link>/edit")
class EditLink(Endpoint):
    def html(self, slug: str, link: str):
        u = self.require_authentication(slug)
        all_tags = u.get_tags()
        l = u.get_link(int(link))
        return render(
            "main",
            v.Page(
                title="login",
                content=render("edit_link", v.SingleLink(l, all_tags)),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/t/<path:tag>")
class GetTaggedLinks(Endpoint):
    def html(self, user: str, tag: str):
        u = m.User.by_slug(user)
        pg = int(flask.request.args.get("page", 1))
        t = u.get_tag(tag)
        links, pages = t.get_links(as_user=self.user, page=pg)
        tags = u.get_related_tags(t)
        linklist = v.LinkList(links=links, pages=pages, tags=tags, user=user)
        return render(
            "main",
            v.Page(
                title=f"tag {tag}",
                content=render("linklist", linklist),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/search/<string:needle>")
class GetStringSearch(Endpoint):
    def html(self, user: str, needle: str):
        u = m.User.by_slug(user)
        pg = int(flask.request.args.get("page", 1))
        links, pages = u.get_string_search(needle=needle, as_user=self.user, page=pg)
        tags = u.get_tags()
        linklist = v.LinkList(links=links, pages=pages, tags=tags, user=user)
        return render(
            "main",
            v.Page(
                title=f"search for '{needle}'",
                content=render("linklist", linklist),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/import")
class PinboardImport(Endpoint):
    def html(self, user: str):
        u = self.require_authentication(user)
        return render(
            "main",
            v.Page(
                title=f"import pinboard data", content=render("import"), user=self.user,
            ),
        )

    def api_post(self, user: str):
        u = self.require_authentication(user)
        if "file" not in flask.request.files:
            raise e.BadFileUpload("could not find attached file")
        file = flask.request.files["file"]
        if file.filename == "":
            raise e.BadFileUpload("no file selected")
        u.import_pinboard_data(file.stream)
        return self.api_ok(u.base_url())

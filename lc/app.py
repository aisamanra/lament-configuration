import contextlib
import os
import flask
import sys

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r
from lc.web import Endpoint, endpoint, render

app = c.app


@endpoint("/")
class Index(Endpoint):
    def html(self):
        return render(
            "main",
            title="main",
            content=render(
                "message",
                title="Lament Configuration",
                message="Bookmark organizing for real pinheads.",
            ),
            user=self.user,
        )


@endpoint("/auth")
class Auth(Endpoint):
    def api_post(self):
        _, token = m.User.login(self.request_data(r.User))
        return {"token": token}


@endpoint("/login")
class Login(Endpoint):
    def html(self):
        return render("main", title="login", content=render("login"), user=self.user)

    def api_post(self):
        req = self.request_data(r.User)
        u, token = m.User.login(req)
        flask.session["auth"] = token
        raise e.LCRedirect(u.base_url())


@endpoint("/logout")
class Logout(Endpoint):
    def html(self):
        if "auth" in flask.session:
            del flask.session["auth"]
        raise e.LCRedirect("/")

    def api_post(self):
        if "auth" in flask.session:
            del flask.session["auth"]
        raise e.LCRedirect("/")


@endpoint("/u")
class CreateUser(Endpoint):
    def html(self):
        if self.user:
            raise e.LCRedirect(f"/u/{self.user.name}")

        token = flask.request.args.get("token")
        if not token:
            raise e.LCRedirect("/")

        return render(
            "main",
            title="add user",
            user=self.user,
            content=render("add_user", token=token),
        )

    def api_post(self):
        token = flask.request.args["token"]
        u = m.User.from_invite(self.request_data(r.NewUser).to_user_request(), token)
        raise e.LCRedirect(u.base_url())


@endpoint("/u/<string:slug>")
class GetUser(Endpoint):
    def html(self, slug: str):
        u = m.User.by_slug(slug)
        pg = int(flask.request.args.get("page", 1))
        links, pages = u.get_links(page=pg)
        return render(
            "main",
            title=f"user {u.name}",
            content=render("linklist", links=links, pages=pages),
            user=self.user,
        )

    def api_get(self, slug: str):
        return m.User.by_slug(slug).to_dict()


@endpoint("/u/<string:user>/config")
class UserConfig(Endpoint):
    def html(self, user: str):
        u = self.require_authentication(user)
        return render(
            "main",
            title="configuration",
            content=render("config", **u.get_config()),
            user=self.user,
        )


@endpoint("/u/<string:user>/invite")
class CreateInvite(Endpoint):
    def api_post(self, user: str):
        u = self.require_authentication(user)
        m.UserInvite.manufacture(u)
        raise e.LCRedirect(f"/u/{user}/config")


@endpoint("/u/<string:user>/l")
class CreateLink(Endpoint):
    def html(self, user: str):
        return render("main", title="login", content=render("add_link"), user=self.user)

    def api_post(self, user: str):
        u = self.require_authentication(user)
        req = self.request_data(r.Link)
        l = m.Link.from_request(u, req)
        raise e.LCRedirect(l.link_url())


@endpoint("/u/<string:user>/l/<string:link>")
class GetLink(Endpoint):
    def api_get(self, user: str, link: str):
        pass

    def html(self, user: str, link: str):
        l = m.User.by_slug(user).get_link(int(link))
        return render(
            "main",
            title=f"link {l.name}",
            content=render("linklist", links=[l]),
            user=self.user,
        )
        pass


@endpoint("/u/<string:user>/t/<path:tag>")
class GetTaggedLinks(Endpoint):
    def html(self, user: str, tag: str):
        u = m.User.by_slug(user)
        pg = int(flask.request.args.get("page", 0))
        t = u.get_tag(tag)
        links, pages = t.get_links(page=pg)
        return render(
            "main",
            title=f"tag {tag}",
            content=render("linklist", links=links, pages=pages),
            user=self.user,
        )

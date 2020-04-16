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

app = c.app


@endpoint("/")
class Index(Endpoint):
    def html(self):
        return render(
            "main",
            v.Page(
                title="main",
                content=render(
                    "message",
                    v.Message(
                        title="Lament Configuration",
                        message="Bookmark organizing for real pinheads.",
                    ),
                ),
                user=self.user,
            ),
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

        return render(
            "main",
            v.Page(title="add user", user=self.user, content=render("add_user"),),
        )

    def api_post(self):
        token = flask.request.args["token"]
        req = self.request_data(r.NewUser).to_user_request()
        u = m.User.from_invite(req, token)
        flask.session["auth"] = req.to_token()
        return self.api_ok(u.base_url(), u)


@endpoint("/u/<string:slug>")
class GetUser(Endpoint):
    def html(self, slug: str):
        u = m.User.by_slug(slug)
        pg = int(flask.request.args.get("page", 1))
        links, pages = u.get_links(as_user=self.user, page=pg)
        return render(
            "main",
            v.Page(
                title=f"user {u.name}",
                content=render("linklist", v.LinkList(links=links, pages=pages)),
                user=self.user,
            ),
        )

    def api_get(self, slug: str):
        return m.User.by_slug(slug).to_dict()


@endpoint("/u/<string:user>/config")
class UserConfig(Endpoint):
    def html(self, user: str):
        u = self.require_authentication(user)
        return render(
            "main",
            v.Page(
                title="configuration",
                content=render("config", u.get_config()),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/invite")
class CreateInvite(Endpoint):
    def api_post(self, user: str):
        u = self.require_authentication(user)
        invite = m.UserInvite.manufacture(u)
        return self.api_ok(f"/u/{user}/config", {"invite": invite.token})


@endpoint("/u/<string:user>/l")
class CreateLink(Endpoint):
    def html(self, user: str):
        return render(
            "main", v.Page(title="login", content=render("add_link"), user=self.user,)
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
        u.get_link(int(link)).delete().execute()
        return self.api_ok(u.base_url())

    def html(self, user: str, link: str):
        l = m.User.by_slug(user).get_link(int(link))
        return render(
            "main",
            v.Page(
                title=f"link {l.name}",
                content=render("linklist", v.LinkList([l.to_view(self.user)])),
                user=self.user,
            ),
        )


@endpoint("/u/<string:slug>/l/<string:link>/edit")
class EditLink(Endpoint):
    def html(self, slug: str, link: str):
        u = self.require_authentication(slug)
        l = u.get_link(int(link))
        return render(
            "main",
            v.Page(
                title="login",
                content=render("edit_link", v.SingleLink(l)),
                user=self.user,
            ),
        )


@endpoint("/u/<string:user>/t/<path:tag>")
class GetTaggedLinks(Endpoint):
    def html(self, user: str, tag: str):
        u = m.User.by_slug(user)
        pg = int(flask.request.args.get("page", 0))
        t = u.get_tag(tag)
        links, pages = t.get_links(as_user=self.user, page=pg)
        return render(
            "main",
            v.Page(
                title=f"tag {tag}",
                content=render("linklist", v.LinkList(links=links, pages=pages,)),
                user=self.user,
            ),
        )

import contextlib
import os
import flask
import pystache
import sys

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r

app = flask.Flask(__name__)
loader = pystache.loader.Loader(extension="mustache", search_dirs=["templates"])


def render(name, **kwargs):
    """Load and use a Mustache template from the project root"""
    template = loader.load_name(name)
    renderer = pystache.Renderer(missing_tags="strict", search_dirs=["templates"])
    return renderer.render(template, kwargs)


class Endpoint:
    def api_post(self, *args, **kwargs) -> dict:
        raise NotImplemented

    def public(self, *args, **kwargs):
        raise NotImplemented

    def private(self, user, *args, **kwargs):
        return flask.redirect("/")

    def route(self, *args, **kwargs):
        if flask.request.method == "POST":
            try:
                return self.api_post(*args, **kwargs)
            except e.LCException as exn:
                return ({"status": exn.http_code(), "error": str(exn)}, exn.http_code())

        try:
            return self.public(*args, **kwargs)
        except e.LCException as exn:
            page = render(
                "main", title="error", content=f"shit's fucked yo: {exn}", user=None,
            )
            return (page, exn.http_code())


def endpoint(cls):
    def func(*args, **kwargs):
        return cls().route(*args, **kwargs)

    func.__name__ = cls.__name__
    return func


@app.route("/")
@endpoint
class Index(Endpoint):
    def public(self):
        return render("main", title="main", content="whoo", user=None)


@app.route("/auth")
@endpoint
class Auth(Endpoint):
    def api_post(self):
        u = m.User.login(r.User.from_json(flask.request.data))
        return flask.redirect(u.base_url())


@app.route("/u")
def create_user():
    print(flask.request.data)
    u = m.User.from_request(r.User.from_json(flask.request.data))
    return flask.redirect(u.base_url())


@app.route("/u/<string:user>")
def get_user(user: str):
    u = m.User.by_slug(user)
    pg = int(flask.request.args.get("page", 0))
    links = u.get_links(page=pg)
    return render(
        "main", title=f"user {u.name}", content=render("linklist", links=links), user=u,
    )


@app.route("/u/<string:user>/l")
def create_link(user: str):
    pass


@app.route("/u/<string:user>/l/<string:link>")
def link(user: str, link: str):
    pass


@app.route("/u/<string:user>/t/<path:tag>")
def get_tagged_links(user: str, tag: str):
    u = m.User.by_slug(user)
    pg = int(flask.request.args.get("page", 0))
    t = u.get_tag(tag)
    links = t.get_links(page=pg)
    return render(
        "main", title=f"tag {tag}", content=render("linklist", links=links), user=u,
    )

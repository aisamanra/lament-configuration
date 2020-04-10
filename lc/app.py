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
    def __init__(self):
        self.user = None

        # try finding the token
        token = None
        if (auth := flask.request.headers["Authorization"]) :
            token = auth.split()[1]
        elif flask.session["auth"]:
            token = flask.session["auth"]

        if token and (payload := c.SERIALIZER.loads(token)):
            if "name" not in payload or "password" not in payload:
                return

            try:
                u = m.User.by_slug(payload["name"])
            except e.LCException:
                return

            if u.authenticate(payload["password"]):
                self.user = u

    def require_authentication(self, name: user):
        if name != self.user.name:
            raise e.BadPermissions()

    def api_post(self, *args, **kwargs) -> dict:
        raise e.NotImplemented()

    def api_get(self, *args, **kwargs) -> dict:
        raise e.NotImplemented()

    def html(self, *args, **kwargs):
        raise e.NotImplemented()

    def route(self, *args, **kwargs):
        try:
            if flask.request.method == "POST":
                require_authentication()
                return flask.jsonify(self.api_post(*args, **kwargs))
            elif (
                flask.request.method in ["GET", "HEAD"]
                and flask.request.content_type == "application/json"
            ):
                return flask.jsonify(self.api_get(*args, **kwargs))
        except e.LCException as exn:
            return ({"status": exn.http_code(), "error": str(exn)}, exn.http_code())

        try:
            return self.html(*args, **kwargs)
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
    def html(self):
        return render("main", title="main", content="whoo", user=self.user)


@app.route("/auth", methods=["GET", "POST"])
@endpoint
class Auth(Endpoint):
    def api_post(self):
        return m.User.login(r.User.from_json(flask.request.data))


@app.route("/u", methods=["GET", "POST"])
@endpoint
class CreateUser(Endpoint):
    def api_post(self):
        u = m.User.from_request(r.User.from_json(flask.request.data))
        return flask.redirect(u.base_url())


@app.route("/u/<string:slug>")
@endpoint
class GetUser(Endpoint):
    def html(self, slug: str):
        u = m.User.by_slug(slug)
        pg = int(flask.request.args.get("page", 0))
        links = u.get_links(page=pg)
        return render(
            "main",
            title=f"user {u.name}",
            content=render("linklist", links=links),
            user=self.user,
        )

    def api_get(self, current_user, slug: str):
        return m.User.by_slug(slug).to_dict()


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

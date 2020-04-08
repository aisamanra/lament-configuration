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


def handle_errors(func):
    def __wrapped__(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except e.LCException as exn:
            return (
                render("main",
                       title="error",
                       content=f"shit's fucked yo: {exn}",
                       user=None
                ),
                500,
            )

    __wrapped__.__name__ = func.__name__
    return __wrapped__


@app.route("/")
@handle_errors
def index():
    return render("main", title="main", content="whoo", u=None)


@app.route("/auth", methods=["POST"])
@handle_errors
def auth():
    u = m.User.login(r.User.from_json(flask.request.data))
    return flask.redirect(u.base_url())


@app.route("/u", methods=["POST"])
@handle_errors
def create_user():
    print(flask.request.data)
    u = m.User.from_request(r.User.from_json(flask.request.data))
    return flask.redirect(u.base_url())


@app.route("/u/<string:user>", methods=["GET", "POST"])
@handle_errors
def get_user(user: str):
    u = m.User.by_slug(user)
    pg = int(flask.request.args.get("page", 0))
    links = u.get_links(page=pg)
    return render(
        "main",
        title=f"user {u.name}",
        content=render("linklist", links=links),
        user=u,
    )


@app.route("/u/<string:user>/l", methods=["POST"])
@handle_errors
def create_link(user: str):
    pass


@app.route("/u/<string:user>/l/<string:link>", methods=["GET", "POST"])
@handle_errors
def link(user: str, link: str):
    pass


@app.route("/u/<string:user>/t/<path:tag>")
@handle_errors
def get_tagged_links(user: str, tag: str):
    u = m.User.by_slug(user)
    pg = int(flask.request.args.get("page", 0))
    t = u.get_tag(tag)
    links = t.get_links(page=pg)
    return render(
        "main",
        title=f"tag {tag}",
        content=render("linklist", links=links),
        user=u,
    )

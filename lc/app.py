import contextlib
import os
import flask
import sys

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r
from lc.web import Endpoint, endpoint, render

app = flask.Flask(__name__)

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

    def api_get(self, slug: str):
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

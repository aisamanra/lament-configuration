import os
import flask
import pystache

import lc.model as m
import lc.request as r

app = flask.Flask(__name__)
loader = pystache.loader.Loader(extension="mustache", search_dirs=["templates"],)

def render(name, **kwargs):
    '''Load and use a Mustache template from the project root'''
    template = loader.load_name(name)
    return pystache.Renderer().render(template, kwargs)



@app.route("/")
def index():
    return render('main', title='main', content='whoo')


@app.route("/u", methods=["POST"])
def create_user():
    print(flask.request.data)
    u = m.User.from_request(r.User.from_json(flask.request.data))
    return flask.redirect(u.base_url())


@app.route("/u/<string:user>", methods=["GET", "POST"])
def get_user(user):
    u = m.User.by_slug(user)
    return render('main', title=f'user {u.name}', content='stuff')


@app.route("/u/<string:user>/l", methods=["POST"])
def create_link(user):
    pass


@app.route("/u/<string:user>/l/<string:link>", methods=["GET", "POST"])
def link(user):
    pass


@app.route("/u/<string:user>/t/<path:tag>")
def get_tagged_links(user, tag):
    pass

import os
import flask
import pystache

import lc.model as m

LOADER = pystache.loader.Loader(
    extension='mustache',
    search_dirs=[os.path.join(PROJ_ROOT, 'templates')],
)

app = flask.Flask(__name__)

@app.route('/')
def index():
    pass

@app.route('/u', methods=['POST'])
def create_user(user):
    pass

@app.route('/u/<string:user>', methods=['GET', 'POST'])
def get_user(user):
    pass

@app.route('/u/<string:user>/l', methods=['POST'])
def create_link(user):
    pass

@app.route('/u/<string:user>/l/<string:link>', methods=['GET', 'POST'])
def link(user):
    pass

@app.route('/u/<string:user>/t/<path:tag>')
def get_tagged_links(user, tag):
    pass

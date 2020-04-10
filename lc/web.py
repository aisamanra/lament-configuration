import flask
import pystache

import lc.config as c
import lc.model as m


class Endpoint:
    def __init__(self):
        self.user = None

        # try finding the token
        token = None
        # first check the HTTP headers
        if (auth := flask.request.headers.get("Authorization", None)):
            token = auth.split()[1]
        # if that fails, check the session
        elif flask.session.get("auth", None):
            token = flask.session["auth"]

        # if that exists and we can deserialize it, then make sure
        # it contains a valid user password, too
        if token and (payload := c.SERIALIZER.loads(token)):
            if "name" not in payload or "password" not in payload:
                return

            try:
                u = m.User.by_slug(payload["name"])
            except e.LCException:
                return

            if u.authenticate(payload["password"]):
                self.user = u

    def require_authentication(self, name: str):
        '''
        Check that the currently logged-in user exists and is the
        same as the user whose username is given. Raises an exception
        otherwise.
        '''
        if not self.user or name != self.user.name:
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


LOADER = pystache.loader.Loader(extension="mustache", search_dirs=["templates"])


def render(name, **kwargs):
    """Load and use a Mustache template from the project root"""
    template = LOADER.load_name(name)
    renderer = pystache.Renderer(missing_tags="strict", search_dirs=["templates"])
    return renderer.render(template, kwargs)

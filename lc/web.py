import flask
import pystache

import lc.config as c
import lc.error as e
import lc.model as m


class Endpoint:
    def __init__(self):
        self.user = None

        # try finding the token
        token = None
        # first check the HTTP headers
        if (auth := flask.request.headers.get("Authorization", None)) :
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

    def request_data(self, cls):
        if flask.request.content_type == "application/json":
            return cls.from_json(flask.request.data)
        elif flask.request.content_type == "application/x-www-form-urlencoded":
            return cls.from_form(flask.request.form)
        else:
            raise e.BadContentType(flask.request.content_type)

    def require_authentication(self, name: str) -> m.User:
        """
        Check that the currently logged-in user exists and is the
        same as the user whose username is given. Raises an exception
        otherwise.
        """
        if not self.user or name != self.user.name:
            raise e.BadPermissions()

        return self.user

    def route(self, *args, **kwargs):
        try:
            if flask.request.method == "POST":
                return flask.jsonify(self.api_post(*args, **kwargs))
            elif (
                flask.request.method in ["GET", "HEAD"]
                and flask.request.content_type == "application/json"
            ):
                return flask.jsonify(self.api_get(*args, **kwargs))
        except e.LCException as exn:
            return ({"status": exn.http_code(), "error": str(exn)}, exn.http_code())
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())

        try:
            return self.html(*args, **kwargs)
        except e.LCException as exn:
            page = render(
                "main", title="error", content=f"shit's fucked yo: {exn}", user=None,
            )
            return (page, exn.http_code())
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())


def endpoint(route):
    def do_endpoint(cls):
        def func(*args, **kwargs):
            return cls().route(*args, **kwargs)

        methods = ["GET"]
        if "api_post" in dir(cls):
            methods.append("POST")

        func.__name__ = cls.__name__
        return c.app.route(route, methods=methods)(func)

    return do_endpoint


LOADER = pystache.loader.Loader(extension="mustache", search_dirs=["templates"])


def render(name, **kwargs):
    """Load and use a Mustache template from the project root"""
    template = LOADER.load_name(name)
    renderer = pystache.Renderer(missing_tags="strict", search_dirs=["templates"])
    return renderer.render(template, kwargs)

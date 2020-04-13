from dataclasses import dataclass
import flask
import pystache
from typing import TypeVar, Type

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r


T = TypeVar("T", bound=r.Request)

@dataclass
class ApiOK:
    response: dict


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
        if token and (payload := c.serializer.loads(token)):
            if "name" not in payload or "password" not in payload:
                return

            try:
                u = m.User.by_slug(payload["name"])
            except e.LCException:
                return

            if u.authenticate(payload["password"]):
                self.user = u

    def api_ok(self, redirect: str, data: dict = {"status": "ok"}) -> ApiOK:
        if flask.request.content_type == "application/json":
            return ApiOK(response=data)
        elif flask.request.content_type == "application/x-www-form-urlencoded":
            raise e.LCRedirect(redirect)
        else:
            raise e.BadContentType(flask.request.content_type or "unknown")

    def request_data(self, cls: Type[T]) -> T:
        """Construct a Request model from either a JSON payload or a urlencoded payload"""
        if flask.request.content_type == "application/json":
            try:
                return cls.from_json(flask.request.data)
            except KeyError as exn:
                raise e.BadPayload(key=exn.args[0])

        elif flask.request.content_type == "application/x-www-form-urlencoded":
            return cls.from_form(flask.request.form)
        else:
            raise e.BadContentType(flask.request.content_type or "unknown")

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
        """Forward to the appropriate routing method"""
        try:
            if flask.request.method == "POST":
                # all POST methods are "API methods": if we want to
                # display information in response to a post, then we
                # should redirect to the page where that information
                # can be viewed instead of returning that
                # information. (I think.)
                api_ok = self.api_post(*args, **kwargs)
                assert isinstance(api_ok, ApiOK)
                return flask.jsonify(api_ok.response)
            elif (
                flask.request.method in ["GET", "HEAD"]
                and flask.request.content_type == "application/json"
            ):
                # Here we're distinguishing between an API GET (i.e. a
                # client trying to get JSON data about an endpoint)
                # versus a user-level GET (i.e. a user in a browser.)
                # I like using the HTTP headers to distinguish these
                # cases, while other APIs tend to have a separate /api
                # endpoint to do this.
                return flask.jsonify(self.api_get(*args, **kwargs))
        # if an exception arose from an "API method", then we should
        # report it as JSON
        except e.LCException as exn:
            if flask.request.content_type == "application/json":
                return ({"status": exn.http_code(), "error": str(exn)}, exn.http_code())
            else:
                page = render(
                    "main", title="error", content=f"shit's fucked yo: {exn}", user=None,
                )
                return (page, exn.http_code())
        # also maybe we tried to redirect, so just do that
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())

        # if we're here, it means we're just trying to get a typical
        # HTML request.
        try:
            return self.html(*args, **kwargs)
        except e.LCException as exn:
            page = render(
                "main", title="error", content=f"shit's fucked yo: {exn}", user=None,
            )
            return (page, exn.http_code())
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())


# Decorators result in some weird code in Python, especially 'cause it
# doesn't make higher-order functions terse. Let's break this down a
# bit. This out method, `endpoint`, takes the route...
def endpoint(route: str):
    """Route an endpoint using our semi-smart routing machinery"""
    # but `endpoint` returns another function which is going to be
    # called with the result of the definition after it. The argument
    # to what we're calling `do_endpoint` here is going to be the
    # class object defined afterwards.
    def do_endpoint(endpoint_class: Type[Endpoint]):
        # we'll just make that explicit here
        assert Endpoint in endpoint_class.__bases__
        # finally, we need a function that we'll give to Flask in
        # order to actually dispatch to. This is the actual routing
        # function, which is why it just creates an instance of the
        # endpoint provided above and calls the `route` method on it
        def func(*args, **kwargs):
            return endpoint_class().route(*args, **kwargs)

        # use reflection over the methods defined by the endpoint
        # class to decide if it needs to accept POST requests or not.
        methods = ["GET"]
        if "api_post" in dir(endpoint_class):
            methods.append("POST")

        # this is just for making error messages nicer
        func.__name__ = endpoint_class.__name__

        # finally, use the Flask routing machinery to register our callback
        return c.app.route(route, methods=methods)(func)

    return do_endpoint


LOADER = pystache.loader.Loader(extension="mustache", search_dirs=["templates"])


def render(name: str, **kwargs) -> str:
    """Load and use a Mustache template from the project root"""
    template = LOADER.load_name(name)
    renderer = pystache.Renderer(missing_tags="strict", search_dirs=["templates"])
    return renderer.render(template, kwargs)

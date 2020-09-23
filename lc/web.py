from dataclasses import dataclass
import flask
import pystache
from typing import Optional, TypeVar, Type

import lc.config as c
import lc.error as e
import lc.model as m
import lc.request as r
import lc.view as v


T = TypeVar("T", bound=r.Request)


@dataclass
class ApiOK:
    response: dict


class Endpoint:
    __slots__ = ("user",)

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

        if token is None:
            return

        # if that exists and we can deserialize it, then make sure
        # it contains a valid user password, too
        try:
            payload = c.app.load_token(token)
        except:
            # TODO: be more specific about what errors we're catching
            # here!
            return

        if "name" not in payload:
            return

        try:
            u = m.User.by_slug(payload["name"])
            self.user = u
        except e.LCException:
            return

    @staticmethod
    def just_get_user() -> Optional[m.User]:
        try:
            return Endpoint().user
        except:
            # this is going to catch everything on the off chance that
            # there's a bug in the user-validation code: this is used
            # in error handlers, so we should be resilient to that!
            return None

    SHOULD_REDIRECT = set(
        (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        )
    )

    def api_ok(self, redirect: str, data: Optional[dict] = None) -> ApiOK:
        if data is None:
            data = {"status": "ok"}
        data["redirect"] = redirect
        content_type = flask.request.content_type or ""
        content_type = content_type.split(";")[0]
        if content_type in Endpoint.SHOULD_REDIRECT:
            raise e.LCRedirect(redirect)
        else:
            return ApiOK(response=data)

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
                api_ok = self.api_post(*args, **kwargs)  # type: ignore
                assert isinstance(api_ok, ApiOK)
                return flask.jsonify(api_ok.response)
            elif flask.request.method == "DELETE":
                return flask.jsonify(self.api_delete(*args, **kwargs).response)  # type: ignore
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
                return flask.jsonify(self.api_get(*args, **kwargs).response)  # type: ignore
        # if an exception arose from an "API method", then we should
        # report it as JSON
        except e.LCException as exn:
            if flask.request.content_type == "application/json":
                return ({"status": exn.http_code(), "error": str(exn)}, exn.http_code())
            else:
                return (self.render_error(exn), exn.http_code())
        # also maybe we tried to redirect, so just do that
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())

        # if we're here, it means we're just trying to get a typical
        # HTML request.
        try:
            return self.html(*args, **kwargs)  # type: ignore
        except e.LCException as exn:
            return (self.render_error(exn), exn.http_code())
        except e.LCRedirect as exn:
            return flask.redirect(exn.to_path())

    def render_error(self, exn: e.LCException) -> str:
        error = v.Error(code=exn.http_code(), message=str(exn))
        page = v.Page(title="error", content=render("error", error), user=self.user)
        return render("main", page)


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
        if "api_delete" in dir(endpoint_class):
            methods.append("DELETE")

        # this is just for making error messages nicer
        func.__name__ = endpoint_class.__name__

        # finally, use the Flask routing machinery to register our callback
        return c.app.app.route(route, methods=methods)(func)

    return do_endpoint


LOADER = pystache.loader.Loader(extension="mustache", search_dirs=["templates"])


def render(name: str, data: Optional[v.View] = None) -> str:
    """Load and use a Mustache template from the project root"""
    template = LOADER.load_name(name)
    renderer = pystache.Renderer(missing_tags="strict", search_dirs=["templates"])
    return renderer.render(template, data or {})


@c.app.app.errorhandler(404)
def handle_404(e):
    user = Endpoint.just_get_user()
    url = flask.request.path
    error = v.Error(code=404, message=f"Page {url} not found")
    page = v.Page(title="not found", content=render("error", error), user=None)
    return render("main", page)


@c.app.app.errorhandler(500)
def handle_500(e):
    user = Endpoint.just_get_user()
    c.log(f"Internal error: {e}")
    error = v.Error(code=500, message=f"An unexpected error occurred")
    page = v.Page(title="500", content=render("error", error), user=None)
    return render("main", page)

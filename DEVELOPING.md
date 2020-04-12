# Utilities

The easiest way to develop and test is to have `poetry` and `invoke` installed. If you don't mind installing them globally, you can run

```bash
# make sure ~/.local/bin is on your path
$ export PATH=$HOME/.local/bin
$ python3 -m pip install --user invoke
$ python3 -m pip install --user poetry
```

If you'd prefer sandboxed installations of tools like `invoke` and `poetry`, the easiest way is to use `pipx`, which automatically installs tools in virtualenvs. You still need to install `pipx` somehow, but it's probably better for the others:

```bash
# make sure ~/.local/bin is on your path
$ export PATH=$HOME/.local/bin
$ python3 -m pip install --user pipx
$ pipx install invoke
$ pipx install poetry
```

Once those are installed, you can run, test, and typecheck the program using the following:

```bash
$ # install all the dependencies into a virtualenv
$ inv install
$
$ # run a local test server
$ inv run
$
$ # run all the tests
$ inv test
$
$ # run mypy to type-check the program
$ inv tc
$
$ # run autoformatter, auto-committing the result iff the
$ # current working tree is otherwise clean
$ inv fmt
$
$ # populate a test DB with test data (i.e. Getty's pinboard links)
$ inv populate
$
$ # run a UWSGI server using a local Unix socket
$ inv uwsgi
```

# Rough Architecture

All this is subject to change as architecture is transient, like shifting water.

`lc.config` contains "configuration" but also basically globals: specifically the database and the Flask application. The database isn't initialized yet: this allows us to e.g. initialize it to an in-memory database for tests and whatnot. Config also contains a convenient and colorful `log` function, for reasons that made sense in my head but which I'm finding hard to articulate now that I'm trying to write it.

`lc.request` contains "request objects": the struct-ish representations of stuff which comes off the wire as JSON. It's kind of a data object container, and right now they're all defined as `dataclasses`.

`lc.error` contains error definitions, mostly defined as `Exception` subclasses that are also `dataclasses`. One of them is sort of special: `lc.error.LCRedirect` takes a string and gets translated into an HTTP redirect by the endpoint machinery described below. The rest of them subclass from `lc.error.LCException`, and for those it's important that they provide a helpful `__str__` method and maybe overload the `http_code` method: those will get turned into responses with the appropriate HTTP code, and the message will either show up as a user-facing HTML page (if the error arose in the web interface) or get stuffed into the error field of a JSON object (if the error arose in an API endpoint.)

`lc.model`: ah, now this is the good shit. This contains the database models, defined as Peewee `Model` subclasses. These also include a bunch of helper methods: some of them are static query methods (like "look up all the links associated with this user and tag") while others are helper methods on instances. Finally, there's a `Pagination` object which isn't exactly a model, but is created from information _derived from_ models, which is why it lives here, and the `create_tables` method, that can initialize all the schemas generated from these models in the database.

`lc.web` contains some gross under-the-hood machinery to make `lc.app` look nice and clean. The big thing it defines is a class called `Endpoint`: this contains a `route` method which expects to be called as part of a `flask` route definition, and uses a combination of the request method, the `Content-Type`, and the set of methods defined on the class to do some under-the-hood data decoding and information shuffling to make the endpoint definitions themselves nicer. This is surfaced as a decorator called `endpoint` which looks a lot like the Flask one. I'll explain `Endpoint` a little more below. This also exports `render`, a nice wrapper over the `pystache` template loader machinery.

Finally, `lc.app` contains the actual endpoint definitions, pulling all the above in along with the pystache templates stored in `templates`.

# Using `endpoint`

A barebones usage of `endpoint` looks like this:

```python
@endpoint("/foo")
class Thing(Endpoint):
  def html(self):
    return "<strong>Hello!</strong>"
```

Some things to note: the class _must_ have a unique name (because the class name, here `Thing`, is used by Flask as part of an internal error-reporting API) and the class _must_ inherit from `Endpoint`. (I might be able to metaprogram that in, but this is better for Mypy anyway.) The existence of the `html` endpoint here means, "Call this method when a user in a web browser is trying to access this page." We can include multiple other handler methods, as well: here's a handwavey worked example:

```python
@endpoint("/user/<str:username>")
class User(Endpoint):
  def html(self, username: str):
    return f"Hello, user <em>{username}</em>!"

  def api_get(self, username: str):
    return {"name": username}

  def api_post(self, username: str):
    raise e.LCRedirect("/")
```

A few things to note: each method needs to have the same exact named arguments, and those named arguments (after `self`) need to be the fragments matched by the URL. The return value from `html` is going to be a string that's interpreted as HTML, while the return values from `api_get` and `api_post` can be an arbitrary Python dictionary that's going to be turned into JSON. In order to indicate that a given handler wants to raise a redirect, we can raise an `LCRedirect` exception, which the handler machinery knows to turn into the appropriate redirect. Also, the fact that this one has `api_post` defined means that Flask will allow `POST` requests to this URL; if we only defined `html` and/or `api_get`, then Flask would know to reject all `POST` requests to that URL to begin with.

Finally, there are a few helper methods on `Endpoint` that aid us in writing terse descriptive endpoints. A new `Endpoint` object is initialized for each route invocation, and it'll contain a `user` instance variable that is `None` if the user is not logged in and a `User` object if there is a logged-in user (either via a web session or via a `Bearer` authentication token.) There's also a helper method `require_authentication` that takes a username and verifies that it is the username of the currently-logged-in user for that session. Finally, `request_data` is a way of abstracting over two different ways of submitting data: as JSON data (for use in an API) and as URLEncoded data (from an HTML form). All the objects defined in `lc.request` should be defined using `dataclasses_json`, which will let us auto-derive JSON serialization/deserialization, and should have a manually implemented constructor method `from_form` which can be used to construct those objects from the flat structures used in HTML forms. (e.g. you don't get lists, you instead need to, say, split apart strings.) `request_data` is given the class you want to construct, and it will return an instance of that class decoded from the data given to the request, or raise an informative error otherwise.

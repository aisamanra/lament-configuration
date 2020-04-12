from dataclasses import dataclass


@dataclass
class LCRedirect(Exception):
    path: str

    def to_path(self) -> str:
        return self.path


class LCException(Exception):
    def to_json(self) -> dict:
        return {"error": str(self)}

    def http_code(self) -> int:
        return 500


@dataclass
class UserExists(LCException):
    name: str

    def __str__(self):
        return f"A user named {self.name} already exists."


@dataclass
class NoSuchUser(LCException):
    name: str

    def __str__(self):
        return f"No user named {self.name} exists."

    def http_code(self) -> int:
        return 404


@dataclass
class BadPassword(LCException):
    name: str

    def __str__(self):
        return f"Wrong password for user {self.name}."

    def http_code(self) -> int:
        return 403


@dataclass
class NotImplemented(LCException):
    def __str__(self):
        return f"Bad request: no handler for route."

    def http_code(self) -> int:
        return 404


@dataclass
class BadPermissions(LCException):
    def __str__(self):
        return f"Insufficient permissions."

    def http_code(self) -> int:
        return 400


@dataclass
class BadContentType(LCException):
    content_type: str

    def __str__(self):
        return f"Bad content type for request: {self.content_type}"

    def http_code(self) -> int:
        return 500

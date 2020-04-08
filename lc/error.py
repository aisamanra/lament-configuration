from dataclasses import dataclass


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

from dataclasses import dataclass

@dataclass
class UserExists(Exception):
    name: str

    def __str__(self):
        return f"A user named {self.name} already exists."

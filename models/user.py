"""User roles and identity models."""

from dataclasses import dataclass


@dataclass
class User:
    username: str
    role: str = "user"


class Admin(User):
    def __init__(self, username: str):
        super().__init__(username, "admin")


class Librarian(User):
    def __init__(self, username: str):
        super().__init__(username, "librarian")

"""Book models, including physical and electronic formats."""

from dataclasses import dataclass


@dataclass
class Book:
    title: str
    author: str
    isbn: str


@dataclass
class PhysicalBook(Book):
    shelf_location: str = ""


@dataclass
class EBook(Book):
    download_url: str = ""

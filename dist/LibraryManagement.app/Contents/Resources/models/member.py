"""Borrower profile model."""

from dataclasses import dataclass


@dataclass
class Member:
    member_id: str
    name: str
    email: str

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Category:
    name: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> Category:
        return cls(name=d["name"])

    COLUMNS = ["name"]

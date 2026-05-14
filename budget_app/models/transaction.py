from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Transaction:
    id: str
    type: Literal["income", "expense"]
    date: str          # YYYY-MM-DD
    amount: int        # 양수
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": str(self.amount),
            "category": self.category,
            "memo": self.memo or "",
            "tags": ";".join(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> Transaction:
        tags_raw = d.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(";") if t.strip()] if tags_raw else []
        return cls(
            id=d["id"],
            type=d["type"],  # type: ignore[arg-type]
            date=d["date"],
            amount=int(d["amount"]),
            category=d["category"],
            memo=d.get("memo", ""),
            tags=tags,
        )

    COLUMNS = ["id", "type", "date", "amount", "category", "memo", "tags"]

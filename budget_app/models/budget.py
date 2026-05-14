from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Budget:
    month: str   # YYYY-MM
    amount: int  # 양수

    def to_dict(self) -> dict[str, str]:
        return {
            "month": self.month,
            "amount": str(self.amount),
        }

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> Budget:
        return cls(
            month=d["month"],
            amount=int(d["amount"]),
        )

    COLUMNS = ["month", "amount"]

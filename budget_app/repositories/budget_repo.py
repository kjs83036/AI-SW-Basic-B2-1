from __future__ import annotations

from pathlib import Path
from typing import Optional

from budget_app.models.budget import Budget
from budget_app.repositories.base import CsvRepository


class BudgetRepository(CsvRepository[Budget]):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir / "budgets.csv", Budget.COLUMNS)

    def get(self, month: str) -> Optional[Budget]:
        for row in self._read_rows():
            if row["month"] == month:
                return Budget.from_dict(row)
        return None

    def set(self, budget: Budget) -> None:
        rows = list(self._read_rows())
        for i, row in enumerate(rows):
            if row["month"] == budget.month:
                rows[i] = budget.to_dict()
                self._write_rows(rows)
                return
        rows.append(budget.to_dict())
        self._write_rows(rows)

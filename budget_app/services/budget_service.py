from __future__ import annotations

from pathlib import Path
from typing import Optional

from budget_app.errors import ValidationError
from budget_app.models.budget import Budget
from budget_app.repositories.budget_repo import BudgetRepository


class BudgetService:
    def __init__(self, data_dir: Path) -> None:
        self._repo = BudgetRepository(data_dir)

    def set_budget(self, month: str, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("예산 금액은 0보다 커야 합니다.")
        budget = Budget(month=month, amount=amount)
        self._repo.set(budget)
        print(f"[저장 완료] {month} 예산 {amount:,}원")

    def get_budget(self, month: str) -> Optional[Budget]:
        return self._repo.get(month)

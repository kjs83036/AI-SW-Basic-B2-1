"""월별 요약 서비스: 총수입/지출/잔액 + 카테고리별 TOP N + 예산 사용률."""
from __future__ import annotations

import heapq
from collections import defaultdict
from pathlib import Path

from budget_app.repositories.transaction_repo import TransactionRepository
from budget_app.services.budget_service import BudgetService


class SummaryService:
    def __init__(self, data_dir: Path) -> None:
        self._tx_repo = TransactionRepository(data_dir)
        self._budget_svc = BudgetService(data_dir)

    def print_monthly(self, month: str, top: int) -> None:
        total_income = 0
        total_expense = 0
        category_expense: dict[str, int] = defaultdict(int)

        has_data = False
        for tx in self._tx_repo.read_all():
            if not tx.date.startswith(month):
                continue
            has_data = True
            if tx.type == "income":
                total_income += tx.amount
            else:
                total_expense += tx.amount
                category_expense[tx.category] += tx.amount

        if not has_data:
            print(f"[{month}] 데이터 없음")
            return

        balance = total_income - total_expense
        print(f"총 수입: {total_income:,}원")
        print(f"총 지출: {total_expense:,}원")
        print(f"잔액: {balance:,}원")

        budget = self._budget_svc.get_budget(month)
        if budget:
            usage_pct = (total_expense / budget.amount * 100) if budget.amount else 0
            print(f"예산: {budget.amount:,}원 (사용률 {usage_pct:.1f}%)")
            if total_expense > budget.amount:
                over = total_expense - budget.amount
                print(f"[경고] 예산 초과! {over:,}원 초과")

        if category_expense:
            top_cats = heapq.nlargest(top, category_expense.items(), key=lambda x: x[1])
            print(f"\n지출 TOP {min(top, len(top_cats))}")
            for i, (cat, amt) in enumerate(top_cats, 1):
                print(f"{i}) {cat} {amt:,}원")

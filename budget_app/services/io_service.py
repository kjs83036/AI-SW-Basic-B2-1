"""CSV import/export 서비스.

외부 스키마 (PDF 고정): date, type, category, amount, memo, tags
내부 저장 스키마: id, type, date, amount, category, memo, tags
"""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Optional

from budget_app.errors import ValidationError
from budget_app.models.transaction import Transaction
from budget_app.repositories.transaction_repo import TransactionRepository
from budget_app.services.category_service import CategoryService

EXPORT_COLUMNS = ["date", "type", "category", "amount", "memo", "tags"]


class IoService:
    def __init__(self, data_dir: Path) -> None:
        self._tx_repo = TransactionRepository(data_dir)
        self._cat_svc = CategoryService(data_dir)

    # ── export ────────────────────────────────────────────────

    def export_csv(
        self,
        out_path: Path,
        month: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> int:
        count = 0
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
            writer.writeheader()
            for tx in self._tx_repo.read_all():
                if month and not tx.date.startswith(month):
                    continue
                if from_date and tx.date < from_date:
                    continue
                if to_date and tx.date > to_date:
                    continue
                writer.writerow({
                    "date": tx.date,
                    "type": tx.type,
                    "category": tx.category,
                    "amount": str(tx.amount),
                    "memo": tx.memo or "",
                    "tags": ",".join(tx.tags),
                })
                count += 1
        return count

    # ── import ────────────────────────────────────────────────

    def import_csv(self, from_path: Path) -> tuple[int, int]:
        if not from_path.exists():
            raise ValidationError(f"파일을 찾을 수 없습니다: {from_path}")

        imported = 0
        skipped = 0
        known_categories = set(self._cat_svc.list_categories())

        with from_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tx = self._row_to_transaction(row, known_categories)
                    self._tx_repo.save(tx)
                    imported += 1
                except (ValidationError, KeyError, ValueError):
                    skipped += 1

        return imported, skipped

    def _row_to_transaction(self, row: dict[str, str], known_categories: set[str]) -> Transaction:
        date_val = row.get("date", "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_val):
            raise ValueError(f"날짜 형식 오류: {date_val}")

        tx_type = row.get("type", "").strip()
        if tx_type not in ("income", "expense"):
            raise ValueError(f"type 오류: {tx_type}")

        category = row.get("category", "").strip()
        if not category:
            raise ValueError("카테고리 없음")

        amount_str = row.get("amount", "").strip()
        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            raise ValueError(f"금액 오류: {amount_str}")

        memo = row.get("memo", "").strip()
        tags_raw = row.get("tags", "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

        tx_id = self._tx_repo.next_id()
        return Transaction(
            id=tx_id,
            type=tx_type,  # type: ignore[arg-type]
            date=date_val,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )

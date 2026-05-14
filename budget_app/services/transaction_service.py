"""거래 서비스: add, list, search, update, delete."""
from __future__ import annotations

import heapq
import re
from datetime import date
from pathlib import Path
from typing import Generator, Optional

from budget_app.errors import NotFoundError, ValidationError
from budget_app.models.transaction import Transaction
from budget_app.prompts import ask, ask_optional
from budget_app.repositories.transaction_repo import TransactionRepository
from budget_app.services.category_service import CategoryService


def _validate_date(s: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)\n[힌트] 예: {date.today().isoformat()}")
    try:
        date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"존재하지 않는 날짜입니다: {s}")
    return s


def _validate_type(s: str) -> str:
    if s not in ("income", "expense"):
        raise ValueError("income 또는 expense만 입력 가능합니다.")
    return s


def _validate_amount(s: str) -> int:
    try:
        n = int(s)
    except ValueError:
        raise ValueError("금액은 정수로 입력하세요.")
    if n <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")
    return n


def _parse_tags(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


class TransactionService:
    def __init__(self, data_dir: Path) -> None:
        self._repo = TransactionRepository(data_dir)
        self._cat_svc = CategoryService(data_dir)

    # ── add (대화형) ────────────────────────────────────────────

    def add_interactive(self) -> Transaction:
        date_val = ask("날짜(YYYY-MM-DD)", validate=_validate_date)
        tx_type = ask("타입(income/expense)", validate=_validate_type)
        category = self._ask_category()
        amount = ask("금액(양수)", validate=_validate_amount)
        memo = ask_optional("메모")
        tags_raw = ask_optional("태그(쉼표로 구분, 없으면 엔터)")
        tags = _parse_tags(tags_raw) if tags_raw else []

        tx_id = self._repo.next_id()
        tx = Transaction(
            id=tx_id,
            type=tx_type,
            date=date_val,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )
        self._repo.save(tx)
        return tx

    def _ask_category(self) -> str:
        names = self._cat_svc.list_categories()
        print(f"[카테고리 목록] {', '.join(names)}")
        while True:
            cat = ask("카테고리")
            if cat in names:
                return cat
            print(f"[오류] 존재하지 않는 카테고리입니다: {cat}")
            print(f"[힌트] 사용 가능: {', '.join(names)}")

    # ── list ──────────────────────────────────────────────────

    def list_transactions(self, limit: int) -> list[Transaction]:
        all_txs = list(self._repo.read_all())
        # 최신순(날짜 내림차순)
        all_txs.sort(key=lambda t: t.date, reverse=True)
        return all_txs[:limit]

    # ── search ────────────────────────────────────────────────

    def search(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        category: Optional[str] = None,
        tx_type: Optional[str] = None,
        query: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Transaction]:
        results = []
        for tx in self._repo.read_all():
            if from_date and tx.date < from_date:
                continue
            if to_date and tx.date > to_date:
                continue
            if category and tx.category != category:
                continue
            if tx_type and tx.type != tx_type:
                continue
            if query and query.lower() not in tx.memo.lower():
                continue
            if tag and tag not in tx.tags:
                continue
            results.append(tx)
        results.sort(key=lambda t: t.date, reverse=True)
        return results

    # ── update ────────────────────────────────────────────────

    def update(
        self,
        tx_id: str,
        date: Optional[str] = None,
        tx_type: Optional[str] = None,
        category: Optional[str] = None,
        amount: Optional[int] = None,
        memo: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Transaction:
        existing: Optional[Transaction] = None
        for tx in self._repo.read_all():
            if tx.id == tx_id:
                existing = tx
                break
        if existing is None:
            raise NotFoundError(f"id={tx_id} 거래를 찾을 수 없습니다.", "list 명령으로 올바른 ID를 확인하세요.")

        if date is not None:
            existing.date = _validate_date(date)
        if tx_type is not None:
            existing.type = _validate_type(tx_type)  # type: ignore[assignment]
        if category is not None:
            self._cat_svc.assert_exists(category)
            existing.category = category
        if amount is not None:
            if amount <= 0:
                raise ValidationError("금액은 0보다 커야 합니다.")
            existing.amount = amount
        if memo is not None:
            existing.memo = memo
        if tags is not None:
            existing.tags = _parse_tags(tags)

        self._repo.update(existing)
        return existing

    # ── delete ────────────────────────────────────────────────

    def delete(self, tx_id: str) -> None:
        if not self._repo.delete(tx_id):
            raise NotFoundError(f"id={tx_id} 거래를 찾을 수 없습니다.", "list 명령으로 올바른 ID를 확인하세요.")

from __future__ import annotations

from pathlib import Path

from budget_app.config import DEFAULT_CATEGORIES
from budget_app.errors import CategoryInUseError, ValidationError
from budget_app.repositories.category_repo import CategoryRepository
from budget_app.repositories.transaction_repo import TransactionRepository


class CategoryService:
    def __init__(self, data_dir: Path) -> None:
        self._cat_repo = CategoryRepository(data_dir)
        self._tx_repo = TransactionRepository(data_dir)
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        if self._cat_repo.is_empty():
            self._cat_repo.seed(DEFAULT_CATEGORIES)
            print("[초기화] 기본 카테고리가 생성되었습니다.")

    def list_categories(self) -> list[str]:
        return self._cat_repo.all_names()

    def add(self, name: str) -> None:
        name = name.strip().lower()
        if not name:
            raise ValidationError("카테고리명이 비어 있습니다.", "예: food, transport")
        if self._cat_repo.exists(name):
            raise ValidationError(f"이미 존재하는 카테고리입니다: {name}")
        self._cat_repo.add(name)
        print(f"[저장 완료] category={name}")

    def remove(self, name: str) -> None:
        name = name.strip().lower()
        if not self._cat_repo.exists(name):
            raise ValidationError(f"존재하지 않는 카테고리입니다: {name}")
        if self._is_in_use(name):
            raise CategoryInUseError(
                f"카테고리 '{name}'은(는) 거래 내역에서 사용 중입니다.",
                "먼저 해당 카테고리의 거래 내역을 삭제하거나 다른 카테고리로 변경하세요.",
            )
        self._cat_repo.remove(name)
        print(f"[완료] 카테고리 '{name}' 삭제되었습니다.")

    def _is_in_use(self, name: str) -> bool:
        for tx in self._tx_repo.read_all():
            if tx.category == name:
                return True
        return False

    def assert_exists(self, name: str) -> None:
        if not self._cat_repo.exists(name):
            names = ", ".join(self._cat_repo.all_names())
            raise ValidationError(
                f"존재하지 않는 카테고리입니다: {name}",
                f"사용 가능한 카테고리: {names}",
            )

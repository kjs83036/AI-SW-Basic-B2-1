import heapq
import json
from pathlib import Path
from typing import Generator, List, Optional

from .models import Budget, Transaction


class TransactionRepository:
    def __init__(self, data_dir: str) -> None:
        self.path = Path(data_dir) / "transactions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._max_id_cache: Optional[int] = None  # import 등 다중 호출 성능 최적화

    def _iter_all(self) -> Generator[Transaction, None, None]:
        """파일을 한 줄씩 읽는 제너레이터 — 전체 로드 없이 스트리밍."""
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Transaction(**json.loads(line))

    def _next_id(self) -> str:
        if self._max_id_cache is None:
            max_num = 0
            for tx in self._iter_all():
                try:
                    num = int(tx.id.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    pass
            self._max_id_cache = max_num
        self._max_id_cache += 1
        return f"TX-{self._max_id_cache:06d}"

    def save(self, tx: Transaction) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(vars(tx)) + "\n")

    def stream(self, limit: Optional[int] = None) -> Generator[Transaction, None, None]:
        """날짜 기준 최신순 스트리밍 (YYYY-MM-DD는 사전식 정렬 = 날짜순).

        limit 지정 시 heapq.nlargest로 상위 N개만 메모리에 유지 —
        전체 리스트를 한 번에 적재하지 않고 제너레이터를 한 줄씩 소비한다.
        """
        if limit is not None:
            top = heapq.nlargest(limit, self._iter_all(), key=lambda tx: tx.date)
            yield from top
        else:
            yield from sorted(self._iter_all(), key=lambda tx: tx.date, reverse=True)

    def get_by_id(self, tx_id: str) -> Optional[Transaction]:
        for tx in self._iter_all():
            if tx.id == tx_id:
                return tx
        return None

    def _rewrite(self, items: List[Transaction]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for tx in items:
                f.write(json.dumps(vars(tx)) + "\n")

    def update(self, tx_id: str, **kwargs) -> bool:
        items = list(self._iter_all())
        updated = False
        for tx in items:
            if tx.id == tx_id:
                for k, v in kwargs.items():
                    setattr(tx, k, v)
                updated = True
                break
        if updated:
            self._rewrite(items)
        return updated

    def delete(self, tx_id: str) -> bool:
        items = list(self._iter_all())
        new_items = [tx for tx in items if tx.id != tx_id]
        if len(new_items) == len(items):
            return False
        self._rewrite(new_items)
        return True


class CategoryStore:
    DEFAULT_CATEGORIES = [
        "food", "transport", "rent", "salary",
        "shopping", "utility", "entertainment",
    ]

    def __init__(self, data_dir: str) -> None:
        self.path = Path(data_dir) / "categories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            self._init_defaults()

    def _init_defaults(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for name in self.DEFAULT_CATEGORIES:
                f.write(json.dumps({"name": name}) + "\n")

    def list_all(self) -> List[str]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line)["name"] for line in f if line.strip()]

    def exists(self, name: str) -> bool:
        return name in self.list_all()

    def add(self, name: str) -> bool:
        if self.exists(name):
            return False
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}) + "\n")
        return True

    def remove(self, name: str) -> bool:
        cats = self.list_all()
        if name not in cats:
            return False
        with open(self.path, "w", encoding="utf-8") as f:
            for c in cats:
                if c != name:
                    f.write(json.dumps({"name": c}) + "\n")
        return True


class BudgetStore:
    def __init__(self, data_dir: str) -> None:
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, month: str) -> Optional[Budget]:
        if not self.path.exists():
            return None
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data["month"] == month:
                        return Budget(**data)
        return None

    def set(self, budget: Budget) -> None:
        budgets: dict = {}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        budgets[data["month"]] = data
        budgets[budget.month] = vars(budget)
        with open(self.path, "w", encoding="utf-8") as f:
            for data in budgets.values():
                f.write(json.dumps(data) + "\n")

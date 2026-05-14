from __future__ import annotations

from pathlib import Path
from typing import Generator

from budget_app.models.category import Category
from budget_app.repositories.base import CsvRepository


class CategoryRepository(CsvRepository[Category]):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir / "categories.csv", Category.COLUMNS)

    def read_all(self) -> Generator[Category, None, None]:
        for row in self._read_rows():
            yield Category.from_dict(row)

    def exists(self, name: str) -> bool:
        return any(row["name"] == name for row in self._read_rows())

    def add(self, name: str) -> None:
        rows = list(self._read_rows())
        rows.append({"name": name})
        self._write_rows(rows)

    def remove(self, name: str) -> bool:
        rows = list(self._read_rows())
        new_rows = [r for r in rows if r["name"] != name]
        if len(new_rows) == len(rows):
            return False
        self._write_rows(new_rows)
        return True

    def all_names(self) -> list[str]:
        return [row["name"] for row in self._read_rows()]

    def is_empty(self) -> bool:
        return self.count() == 0

    def seed(self, names: list[str]) -> None:
        rows = [{"name": n} for n in names]
        self._write_rows(rows)

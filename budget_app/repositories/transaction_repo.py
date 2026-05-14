from __future__ import annotations

from pathlib import Path
from typing import Generator

from budget_app.models.transaction import Transaction
from budget_app.repositories.base import CsvRepository


class TransactionRepository(CsvRepository[Transaction]):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir / "transactions.csv", Transaction.COLUMNS)

    def read_all(self) -> Generator[Transaction, None, None]:
        for row in self._read_rows():
            yield Transaction.from_dict(row)

    def save(self, tx: Transaction) -> None:
        rows = list(self._read_rows())
        rows.append(tx.to_dict())
        self._write_rows(rows)

    def update(self, tx: Transaction) -> bool:
        rows = list(self._read_rows())
        found = False
        for i, row in enumerate(rows):
            if row["id"] == tx.id:
                rows[i] = tx.to_dict()
                found = True
                break
        if found:
            self._write_rows(rows)
        return found

    def delete(self, tx_id: str) -> bool:
        rows = list(self._read_rows())
        new_rows = [r for r in rows if r["id"] != tx_id]
        if len(new_rows) == len(rows):
            return False
        self._write_rows(new_rows)
        return True

    def next_id(self) -> str:
        max_n = 0
        for row in self._read_rows():
            try:
                n = int(row["id"].replace("TX-", ""))
                if n > max_n:
                    max_n = n
            except (ValueError, KeyError):
                pass
        return f"TX-{max_n + 1:06d}"

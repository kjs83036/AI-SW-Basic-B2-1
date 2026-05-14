"""CSV 기반 저장소 기반 클래스.

읽기: csv.DictReader 기반 yield (제너레이터 스트리밍)
쓰기: tmp 파일 → os.replace 원자적 교체
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Generator, Generic, TypeVar

T = TypeVar("T")


class CsvRepository(Generic[T]):
    def __init__(self, path: Path, columns: list[str]) -> None:
        self._path = path
        self._columns = columns
        self._ensure_file()

    def _ensure_file(self) -> None:
        """파일이 없으면 헤더만 있는 빈 CSV 생성."""
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._columns)
                writer.writeheader()

    def _read_rows(self) -> Generator[dict[str, str], None, None]:
        with self._path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield dict(row)

    def _write_rows(self, rows: list[dict[str, str]]) -> None:
        """tmp → os.replace 원자적 교체."""
        tmp = self._path.with_suffix(".csv.tmp")
        try:
            with tmp.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._columns)
                writer.writeheader()
                writer.writerows(rows)
            os.replace(tmp, self._path)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise

    def count(self) -> int:
        return sum(1 for _ in self._read_rows())

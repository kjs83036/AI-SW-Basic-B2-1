import csv
import functools
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Budget, Transaction
from .repository import BudgetStore, CategoryStore, TransactionRepository


def handle_errors(func):
    """예기치 않은 예외를 스택트레이스 없이 [오류]+[힌트] 형식으로 출력."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SystemExit:
            raise
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            print(f"[오류] {e}")
            print("[힌트] 입력값을 확인하세요.")
            sys.exit(1)
    return wrapper


def _fmt_row(tx: Transaction) -> str:
    """거래 1건을 파이프 구분 형식으로 반환. 열 수 항상 6개."""
    return " | ".join([tx.id, tx.date, tx.type, tx.category, str(tx.amount), tx.memo])


class BudgetService:
    def __init__(self, data_dir: str) -> None:
        self.tx_repo = TransactionRepository(data_dir)
        self.cat_store = CategoryStore(data_dir)
        self.budget_store = BudgetStore(data_dir)

    # ── 입력 검증 헬퍼 ─────────────────────────────────────────────────────

    @staticmethod
    def _validate_date(s: str) -> str:
        """날짜 검증 후 정규화(YYYY-MM-DD)."""
        try:
            return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
            print("[힌트] 예: 2024-01-15")
            sys.exit(1)

    @staticmethod
    def _validate_amount(s: str) -> int:
        try:
            v = int(s)
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            print("[오류] 금액은 양수 정수여야 합니다.")
            print("[힌트] 예: 15000")
            sys.exit(1)

    @staticmethod
    def _validate_type(s: str) -> str:
        if s not in ("income", "expense"):
            print("[오류] 타입은 income 또는 expense여야 합니다.")
            print("[힌트] 예: expense")
            sys.exit(1)
        return s

    @staticmethod
    def _validate_month(s: str) -> str:
        try:
            datetime.strptime(s, "%Y-%m")
            return s
        except ValueError:
            print("[오류] 월 형식이 올바르지 않습니다 (YYYY-MM).")
            print("[힌트] 예: 2024-01")
            sys.exit(1)

    # ── 명령 구현 ──────────────────────────────────────────────────────────

    @handle_errors
    def add(self) -> None:
        date = self._validate_date(input("날짜(YYYY-MM-DD): ").strip())
        type_ = self._validate_type(input("타입(income/expense): ").strip())

        while True:
            category = input("카테고리: ").strip()
            if self.cat_store.exists(category):
                break
            cats = self.cat_store.list_all()
            print("[오류] 등록되지 않은 카테고리입니다.")
            print(f"[힌트] 등록된 카테고리: {', '.join(cats)}")
            ans = input("재입력(r) 또는 종료(q)? ").strip()
            if ans == "q":
                sys.exit(1)

        amount = self._validate_amount(input("금액(양수): ").strip())
        memo = input("메모(선택): ").strip()
        tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

        tx_id = self.tx_repo._next_id()
        self.tx_repo.save(Transaction(
            id=tx_id, type=type_, date=date, amount=amount,
            category=category, memo=memo, tags=tags,
        ))
        print(f"[저장 완료] id={tx_id}")

    @handle_errors
    def list_transactions(self, limit: Optional[int] = None) -> None:
        found = False
        for tx in self.tx_repo.stream(limit):
            found = True
            print(_fmt_row(tx))
        if not found:
            print("데이터 없음")

    @handle_errors
    def search(
        self,
        from_: Optional[str],
        to_: Optional[str],
        category: Optional[str],
        type_: Optional[str],
        q: Optional[str],
        tag: Optional[str],
    ) -> None:
        # _iter_all() 제너레이터를 한 줄씩 소비하며 조건 불일치는 즉시 버린다.
        # 전체가 아니라 '매칭된 거래'만 누적 → 최신순 정렬은 매칭 부분집합에만 적용.
        matches = []
        for tx in self.tx_repo._iter_all():
            if from_ and tx.date < from_:
                continue
            if to_ and tx.date > to_:
                continue
            if category and tx.category != category:
                continue
            if type_ and tx.type != type_:
                continue
            if q and q not in tx.memo:
                continue
            if tag:
                tx_tags = [t.strip() for t in tx.tags.split(",") if t.strip()]
                if tag not in tx_tags:
                    continue
            matches.append(tx)

        if not matches:
            print("검색 결과 없음")
            return
        matches.sort(key=lambda t: t.date, reverse=True)
        for tx in matches:
            print(_fmt_row(tx))

    @handle_errors
    def summary(self, month: str, top_n: Optional[int] = None) -> None:
        self._validate_month(month)
        total_income = 0
        total_expense = 0
        category_expense: dict[str, int] = {}

        for tx in self.tx_repo._iter_all():
            if not tx.date.startswith(month):
                continue
            if tx.type == "income":
                total_income += tx.amount
            else:
                total_expense += tx.amount
                category_expense[tx.category] = (
                    category_expense.get(tx.category, 0) + tx.amount
                )

        if total_income == 0 and total_expense == 0:
            print("데이터 없음")
            return

        print(f"총 수입: {total_income}원")
        print(f"총 지출: {total_expense}원")
        print(f"잔액: {total_income - total_expense}원")

        budget = self.budget_store.get(month)
        if budget:
            usage = (total_expense / budget.amount * 100) if budget.amount > 0 else 0.0
            print(f"예산: {budget.amount}원 (사용률 {usage:.1f}%)")
            if total_expense > budget.amount:
                print(f"[경고] 예산 초과! {total_expense - budget.amount}원 초과")

        if category_expense:
            sorted_cats = sorted(
                category_expense.items(), key=lambda x: x[1], reverse=True
            )
            n = top_n if top_n else len(sorted_cats)
            print(f"\n지출 TOP {n}")
            for i, (cat, amt) in enumerate(sorted_cats[:n], 1):
                print(f"{i}) {cat} {amt}원")

    @handle_errors
    def budget_set(self, month: str, amount: int) -> None:
        self._validate_month(month)
        amount = self._validate_amount(str(amount))
        self.budget_store.set(Budget(month=month, amount=amount))
        print(f"[저장 완료] {month} 예산 {amount}원")

    @handle_errors
    def category_add(self, name: str) -> None:
        if not name.strip():
            print("[오류] 카테고리명은 공백일 수 없습니다.")
            sys.exit(1)
        if self.cat_store.add(name):
            print(f"[저장 완료] category={name}")
        else:
            print(f"[오류] 카테고리 '{name}'이(가) 이미 존재합니다.")
            sys.exit(1)

    @handle_errors
    def category_list(self) -> None:
        for c in self.cat_store.list_all():
            print(f"- {c}")

    @handle_errors
    def category_remove(self, name: str) -> None:
        for tx in self.tx_repo._iter_all():
            if tx.category == name:
                print(f"[오류] 카테고리 '{name}'은(는) 사용 중입니다.")
                print("[힌트] 해당 카테고리의 거래를 먼저 삭제하거나 수정하세요.")
                sys.exit(1)
        if self.cat_store.remove(name):
            print(f"[완료] category={name} 삭제됨")
        else:
            print(f"[오류] 카테고리 '{name}'을(를) 찾을 수 없습니다.")
            sys.exit(1)

    @handle_errors
    def update(self, tx_id: str, **kwargs) -> None:
        if not self.tx_repo.get_by_id(tx_id):
            print(f"[오류] id={tx_id}를 찾을 수 없습니다.")
            sys.exit(1)
        if "date" in kwargs:
            kwargs["date"] = self._validate_date(kwargs["date"])
        if "amount" in kwargs:
            kwargs["amount"] = self._validate_amount(str(kwargs["amount"]))
        if "type" in kwargs:
            self._validate_type(kwargs["type"])
        if "category" in kwargs and not self.cat_store.exists(kwargs["category"]):
            print("[오류] 등록되지 않은 카테고리입니다.")
            sys.exit(1)
        self.tx_repo.update(tx_id, **kwargs)
        print(f"[수정 완료] id={tx_id}")

    @handle_errors
    def delete(self, tx_id: str) -> None:
        if self.tx_repo.delete(tx_id):
            print(f"[삭제 완료] id={tx_id}")
        else:
            print(f"[오류] id={tx_id}를 찾을 수 없습니다.")
            sys.exit(1)

    @handle_errors
    def export_csv(
        self,
        out_path: str,
        month: Optional[str] = None,
        from_: Optional[str] = None,
        to_: Optional[str] = None,
    ) -> None:
        rows = []
        for tx in self.tx_repo._iter_all():
            if month and not tx.date.startswith(month):
                continue
            if from_ and tx.date < from_:
                continue
            if to_ and tx.date > to_:
                continue
            rows.append(tx)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
            for tx in rows:
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, tx.tags])

        print(f"[완료] {out_path} ({len(rows)} records)")

    @handle_errors
    def import_csv(self, from_path: str) -> None:
        if not Path(from_path).exists():
            print(f"[오류] 파일을 찾을 수 없습니다: {from_path}")
            sys.exit(1)

        imported = 0
        skipped = 0

        with open(from_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # 1. 헤더 검증 (최소 스키마 고정)
            expected_headers = ["date", "type", "category", "amount", "memo", "tags"]
            if not reader.fieldnames or not all(h in reader.fieldnames for h in expected_headers):
                print("[오류] 올바르지 않은 CSV 스키마입니다. 필수 스키마 헤더(date, type, category, amount, memo, tags)가 누락되었습니다.")
                sys.exit(1)

            for row in reader:
                try:
                    # 2. 필수 값 누락 검증 (Y)
                    if (not row.get("date") or 
                        not row.get("type") or 
                        not row.get("category") or 
                        not row.get("amount")):
                        raise ValueError("필수 컬럼의 값이 누락되었습니다.")

                    date = datetime.strptime(row["date"].strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
                    type_ = row["type"].strip()
                    if type_ not in ("income", "expense"):
                        raise ValueError(f"잘못된 타입: {type_}")
                    
                    amount = int(row["amount"].strip())
                    if amount <= 0:
                        raise ValueError("금액은 양수여야 합니다")
                    
                    category = row["category"].strip()
                    if not category:
                        raise ValueError("카테고리가 비어있습니다")
                        
                    if not self.cat_store.exists(category):
                        self.cat_store.add(category)
                    
                    # 3. 선택 값 기본값 처리 (N)
                    memo = row.get("memo", "").strip() if row.get("memo") else ""
                    tags = row.get("tags", "").strip() if row.get("tags") else ""
                    
                    # 중복검사 추가
                    is_duplicate = False
                    for existing_tx in self.tx_repo._iter_all():
                        if (existing_tx.date == date and 
                            existing_tx.amount == amount and 
                            existing_tx.category == category and 
                            existing_tx.memo == memo):
                            is_duplicate = True
                            break

                    if is_duplicate:
                        skipped += 1
                        continue

                    tx_id = self.tx_repo._next_id()
                    self.tx_repo.save(Transaction(
                        id=tx_id, type=type_, date=date, amount=amount,
                        category=category,
                        memo=memo,
                        tags=tags,
                    ))
                    imported += 1
                except (KeyError, ValueError):
                    skipped += 1

        print(f"[완료] imported={imported}, skipped={skipped}")

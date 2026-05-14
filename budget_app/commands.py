"""CLI 명령 핸들러 — 각 cmd_* 함수가 서비스 계층을 호출한다."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from budget_app.decorators import handle_errors, log_run, set_log_path, timed
from budget_app.config import LOG_FILE


def _init_logging(data_dir: Path) -> None:
    set_log_path(data_dir / LOG_FILE)


# ──────────────────────────────────────────────────────────────
# Phase 4
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_add(data_dir: Path) -> None:
    _init_logging(data_dir)
    from budget_app.services.transaction_service import TransactionService
    svc = TransactionService(data_dir)
    tx = svc.add_interactive()
    print(f"[저장 완료] id={tx.id}")


@handle_errors
@log_run
@timed
def cmd_list(data_dir: Path, limit: int) -> None:
    _init_logging(data_dir)
    from budget_app.services.transaction_service import TransactionService
    svc = TransactionService(data_dir)
    count = 0
    for tx in svc.list_transactions(limit):
        tags_str = ",".join(tx.tags) if tx.tags else ""
        print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {tx.memo} | {tags_str}")
        count += 1
    if count == 0:
        print("거래 내역이 없습니다.")


# ──────────────────────────────────────────────────────────────
# Phase 5
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_search(data_dir: Path, args: argparse.Namespace) -> None:
    _init_logging(data_dir)
    from budget_app.services.transaction_service import TransactionService
    svc = TransactionService(data_dir)
    count = 0
    for tx in svc.search(
        from_date=args.from_date,
        to_date=args.to_date,
        category=args.category,
        tx_type=args.tx_type,
        query=args.query,
        tag=args.tag,
    ):
        tags_str = ",".join(tx.tags) if tx.tags else ""
        print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {tx.memo} | {tags_str}")
        count += 1
    if count == 0:
        print("검색 결과가 없습니다.")


@handle_errors
@log_run
@timed
def cmd_summary(data_dir: Path, month: str, top: int) -> None:
    _init_logging(data_dir)
    from budget_app.services.summary_service import SummaryService
    svc = SummaryService(data_dir)
    svc.print_monthly(month, top)


@handle_errors
@log_run
@timed
def cmd_budget(data_dir: Path, args: argparse.Namespace) -> None:
    _init_logging(data_dir)
    from budget_app.services.budget_service import BudgetService
    svc = BudgetService(data_dir)
    if args.budget_action == "set":
        svc.set_budget(args.month, args.amount)


# ──────────────────────────────────────────────────────────────
# Phase 3
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_category(data_dir: Path, args: argparse.Namespace) -> None:
    _init_logging(data_dir)
    from budget_app.services.category_service import CategoryService
    from budget_app.prompts import ask
    svc = CategoryService(data_dir)

    if args.cat_action == "list":
        names = svc.list_categories()
        if names:
            for n in names:
                print(f"- {n}")
        else:
            print("카테고리가 없습니다.")

    elif args.cat_action == "add":
        name = args.name or ask("카테고리명")
        svc.add(name)

    elif args.cat_action == "remove":
        name = args.name or ask("삭제할 카테고리명")
        svc.remove(name)


# ──────────────────────────────────────────────────────────────
# Phase 6
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_update(data_dir: Path, args: argparse.Namespace) -> None:
    _init_logging(data_dir)
    from budget_app.services.transaction_service import TransactionService
    svc = TransactionService(data_dir)
    svc.update(
        tx_id=args.id,
        date=args.date,
        tx_type=args.tx_type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )
    print(f"[수정 완료] id={args.id}")


@handle_errors
@log_run
@timed
def cmd_delete(data_dir: Path, tx_id: str) -> None:
    _init_logging(data_dir)
    from budget_app.services.transaction_service import TransactionService
    svc = TransactionService(data_dir)
    svc.delete(tx_id)
    print(f"[삭제 완료] id={tx_id}")


# ──────────────────────────────────────────────────────────────
# Phase 7
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_import(data_dir: Path, from_file: str) -> None:
    _init_logging(data_dir)
    from budget_app.services.io_service import IoService
    svc = IoService(data_dir)
    imported, skipped = svc.import_csv(Path(from_file))
    print(f"[완료] imported={imported}, skipped={skipped}")


@handle_errors
@log_run
@timed
def cmd_export(data_dir: Path, args: argparse.Namespace) -> None:
    _init_logging(data_dir)
    from budget_app.services.io_service import IoService
    svc = IoService(data_dir)
    count = svc.export_csv(
        out_path=Path(args.out),
        month=args.month,
        from_date=getattr(args, "from_date", None),
        to_date=getattr(args, "to_date", None),
    )
    print(f"[완료] {args.out} ({count} records)")


# ──────────────────────────────────────────────────────────────
# 보너스
# ──────────────────────────────────────────────────────────────

@handle_errors
@log_run
@timed
def cmd_backup(data_dir: Path) -> None:
    _init_logging(data_dir)
    import shutil
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / f"backup_{ts}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in data_dir.glob("*.csv"):
        shutil.copy2(f, backup_dir / f.name)
    print(f"[백업 완료] {backup_dir}")

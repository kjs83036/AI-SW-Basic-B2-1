import argparse
import sys
from pathlib import Path

from budget_app.config import DEFAULT_DATA_DIR, DEFAULT_LIMIT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        metavar="DIR",
        help=f"데이터 저장 디렉터리 (기본값: {DEFAULT_DATA_DIR})",
    )

    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # add
    sub.add_parser("add", help="거래 추가 (대화형)")

    # list
    p_list = sub.add_parser("list", help="거래 목록 조회")
    p_list.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"출력 개수 (기본값: {DEFAULT_LIMIT})")

    # search
    p_search = sub.add_parser("search", help="거래 검색")
    p_search.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD", help="시작 날짜")
    p_search.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD", help="종료 날짜")
    p_search.add_argument("--category", help="카테고리")
    p_search.add_argument("--type", dest="tx_type", choices=["income", "expense"], help="거래 타입")
    p_search.add_argument("-q", dest="query", help="메모 키워드")
    p_search.add_argument("--tag", help="태그")

    # update
    p_update = sub.add_parser("update", help="거래 수정 (옵션 기반)")
    p_update.add_argument("--id", required=True, help="수정할 거래 ID")
    p_update.add_argument("--date", help="날짜 (YYYY-MM-DD)")
    p_update.add_argument("--type", dest="tx_type", choices=["income", "expense"], help="거래 타입")
    p_update.add_argument("--category", help="카테고리")
    p_update.add_argument("--amount", type=int, help="금액")
    p_update.add_argument("--memo", help="메모")
    p_update.add_argument("--tags", help="태그 (쉼표 구분)")

    # delete
    p_delete = sub.add_parser("delete", help="거래 삭제")
    p_delete.add_argument("--id", required=True, help="삭제할 거래 ID")

    # summary
    p_summary = sub.add_parser("summary", help="월별 요약")
    p_summary.add_argument("--month", required=True, metavar="YYYY-MM", help="대상 월")
    p_summary.add_argument("--top", type=int, default=5, metavar="N", help="카테고리별 TOP N (기본값: 5)")

    # budget
    p_budget = sub.add_parser("budget", help="예산 설정/조회")
    budget_sub = p_budget.add_subparsers(dest="budget_action", metavar="action")
    budget_sub.required = True
    p_budget_set = budget_sub.add_parser("set", help="예산 설정")
    p_budget_set.add_argument("--month", required=True, metavar="YYYY-MM", help="대상 월")
    p_budget_set.add_argument("--amount", required=True, type=int, help="예산 금액")

    # category
    p_cat = sub.add_parser("category", help="카테고리 관리")
    cat_sub = p_cat.add_subparsers(dest="cat_action", metavar="action")
    cat_sub.required = True
    cat_sub.add_parser("list", help="카테고리 목록")
    p_cat_add = cat_sub.add_parser("add", help="카테고리 추가")
    p_cat_add.add_argument("name", nargs="?", help="카테고리명")
    p_cat_remove = cat_sub.add_parser("remove", help="카테고리 삭제")
    p_cat_remove.add_argument("name", nargs="?", help="카테고리명")

    # import
    p_import = sub.add_parser("import", help="CSV 가져오기")
    p_import.add_argument("--from", dest="from_file", required=True, metavar="FILE", help="가져올 CSV 파일")

    # export
    p_export = sub.add_parser("export", help="CSV 내보내기")
    p_export.add_argument("--out", required=True, metavar="FILE", help="저장할 CSV 파일")
    p_export_group = p_export.add_mutually_exclusive_group(required=True)
    p_export_group.add_argument("--month", metavar="YYYY-MM", help="대상 월")
    p_export_group.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD", help="시작 날짜")
    p_export.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD", help="종료 날짜")

    # backup (보너스)
    sub.add_parser("backup", help="데이터 백업")

    return parser


def dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    from budget_app.commands import (
        cmd_add, cmd_list, cmd_search, cmd_update, cmd_delete,
        cmd_summary, cmd_budget, cmd_category, cmd_import, cmd_export,
        cmd_backup,
    )

    data_dir: Path = args.data_dir

    cmd_map = {
        "add": lambda: cmd_add(data_dir),
        "list": lambda: cmd_list(data_dir, args.limit),
        "search": lambda: cmd_search(data_dir, args),
        "update": lambda: cmd_update(data_dir, args),
        "delete": lambda: cmd_delete(data_dir, args.id),
        "summary": lambda: cmd_summary(data_dir, args.month, args.top),
        "budget": lambda: cmd_budget(data_dir, args),
        "category": lambda: cmd_category(data_dir, args),
        "import": lambda: cmd_import(data_dir, args.from_file),
        "export": lambda: cmd_export(data_dir, args),
        "backup": lambda: cmd_backup(data_dir),
    }

    handler = cmd_map.get(args.command)
    if handler:
        handler()
    else:
        parser.print_help()
        sys.exit(1)

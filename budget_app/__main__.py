import argparse
import sys

from .service import BudgetService

DEFAULT_DATA_DIR = "./data"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="데이터 저장 폴더 (기본: ./data)",
    )
    sub = parser.add_subparsers(dest="command")

    # add
    sub.add_parser("add", help="거래 추가 (대화형)")

    # list
    list_p = sub.add_parser("list", help="거래 목록 조회")
    list_p.add_argument("--limit", type=int_or_none, default=10, metavar="N",
                        help="표시할 최대 개수 (기본: 10)")

    # search
    search_p = sub.add_parser("search", help="거래 검색")
    search_p.add_argument("--from", dest="from_", metavar="YYYY-MM-DD", help="시작 날짜")
    search_p.add_argument("--to", dest="to_", metavar="YYYY-MM-DD", help="종료 날짜")
    search_p.add_argument("--category", help="카테고리 필터")
    search_p.add_argument("--type", dest="type_",
                          choices=["income", "expense"], help="거래 타입")
    search_p.add_argument("--q", metavar="키워드", help="메모 키워드 검색")
    search_p.add_argument("--tag", help="태그 검색")

    # summary
    summary_p = sub.add_parser("summary", help="월별 요약")
    summary_p.add_argument("--month", required=True, metavar="YYYY-MM", help="요약할 월")
    summary_p.add_argument("--top", type=int, metavar="N", help="지출 TOP N 카테고리")

    # budget
    budget_p = sub.add_parser("budget", help="예산 관리")
    budget_sub = budget_p.add_subparsers(dest="budget_cmd")
    budget_set_p = budget_sub.add_parser("set", help="예산 설정")
    budget_set_p.add_argument("--month", required=True, metavar="YYYY-MM", help="예산 월")
    budget_set_p.add_argument("--amount", type=int, required=True, help="예산 금액")

    # category
    cat_p = sub.add_parser("category", help="카테고리 관리")
    cat_sub = cat_p.add_subparsers(dest="cat_cmd")
    cat_sub.add_parser("add", help="카테고리 추가 (대화형)")
    cat_sub.add_parser("list", help="카테고리 목록")
    cat_rem_p = cat_sub.add_parser("remove", help="카테고리 삭제 (대화형)")
    cat_rem_p  # noqa: 미사용 경고 억제

    # update (안 A: 옵션 기반으로 고정)
    update_p = sub.add_parser("update", help="거래 수정 (옵션 기반)")
    update_p.add_argument("--id", required=True, help="수정할 거래 ID")
    update_p.add_argument("--date", metavar="YYYY-MM-DD", help="날짜")
    update_p.add_argument("--type", dest="type_",
                          choices=["income", "expense"], help="타입")
    update_p.add_argument("--category", help="카테고리")
    update_p.add_argument("--amount", type=int, help="금액")
    update_p.add_argument("--memo", help="메모")
    update_p.add_argument("--tags", help="태그 (쉼표 구분)")

    # delete
    delete_p = sub.add_parser("delete", help="거래 삭제")
    delete_p.add_argument("--id", required=True, help="삭제할 거래 ID")

    # export
    export_p = sub.add_parser("export", help="CSV 내보내기")
    export_p.add_argument("--out", required=True, metavar="파일경로", help="출력 CSV 파일 경로")
    export_p.add_argument("--month", metavar="YYYY-MM", help="월 필터")
    export_p.add_argument("--from", dest="from_", metavar="YYYY-MM-DD", help="시작 날짜")
    export_p.add_argument("--to", dest="to_", metavar="YYYY-MM-DD", help="종료 날짜")

    # import
    import_p = sub.add_parser("import", help="CSV 가져오기")
    import_p.add_argument("--from", dest="from_", required=True,
                          metavar="파일경로", help="가져올 CSV 파일 경로")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        svc = BudgetService(args.data_dir)
        _dispatch(args, svc, budget_p, cat_p)
    except (KeyboardInterrupt, EOFError):
        print("\n[종료]")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[오류] {e}")
        print("[힌트] 입력값을 확인하세요.")
        sys.exit(1)


def _dispatch(args, svc: BudgetService, budget_p, cat_p) -> None:
    cmd = args.command

    if cmd == "add":
        svc.add()

    elif cmd == "list":
        svc.list_transactions(args.limit)

    elif cmd == "search":
        svc.search(args.from_, args.to_, args.category, args.type_, args.q, args.tag)

    elif cmd == "summary":
        svc.summary(args.month, args.top)

    elif cmd == "budget":
        if getattr(args, "budget_cmd", None) == "set":
            svc.budget_set(args.month, args.amount)
        else:
            budget_p.print_help()

    elif cmd == "category":
        cat_cmd = getattr(args, "cat_cmd", None)
        if cat_cmd == "add":
            name = input("카테고리명: ").strip()
            svc.category_add(name)
        elif cat_cmd == "list":
            svc.category_list()
        elif cat_cmd == "remove":
            name = input("삭제할 카테고리명: ").strip()
            svc.category_remove(name)
        else:
            cat_p.print_help()

    elif cmd == "update":
        kwargs: dict = {}
        if args.date:
            kwargs["date"] = args.date
        if args.type_:
            kwargs["type"] = args.type_
        if args.category:
            kwargs["category"] = args.category
        if args.amount is not None:
            kwargs["amount"] = args.amount
        if args.memo is not None:
            kwargs["memo"] = args.memo
        if args.tags is not None:
            kwargs["tags"] = args.tags
        if not kwargs:
            print("[오류] 수정할 필드를 하나 이상 지정하세요.")
            sys.exit(1)
        svc.update(args.id, **kwargs)

    elif cmd == "delete":
        svc.delete(args.id)

    elif cmd == "export":
        if not args.month and not (args.from_ or args.to_):
            print("[오류] --month 또는 --from/--to 중 하나 이상 필요합니다.")
            sys.exit(1)
        svc.export_csv(args.out, args.month, args.from_, args.to_)

    elif cmd == "import":
        svc.import_csv(args.from_)

def int_or_none(value: str):
    if value.lower() == 'none':
        return None
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}'는 올바른 숫자나 'none'이 아닙니다.")


if __name__ == "__main__":
    main()

import sys
from budget_app.cli import build_parser, dispatch


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch(args, parser)


if __name__ == "__main__":
    main()

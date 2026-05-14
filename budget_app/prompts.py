"""대화형 입력 헬퍼 — 검증 루프가 있는 ask() 래퍼."""
from __future__ import annotations

from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def ask(
    prompt: str,
    *,
    required: bool = True,
    validate: Optional[Callable[[str], T]] = None,
    default: Optional[str] = None,
) -> T:
    """입력값을 받아 validate 통과 시 반환. 실패 시 재입력 요구.

    validate: str → T or raise ValueError(hint)
    """
    display = prompt
    if default is not None:
        display = f"{prompt} (기본값: {default})"
    display += ": "

    while True:
        try:
            raw = input(display).strip()
        except EOFError:
            raw = ""
        if not raw:
            if default is not None:
                raw = default
            elif not required:
                return raw  # type: ignore[return-value]
            else:
                print("[오류] 필수 입력입니다.")
                continue
        if validate is not None:
            try:
                return validate(raw)
            except ValueError as e:
                print(f"[오류] {e}")
                if "(예:" in str(e) or "힌트" in str(e).lower():
                    pass
                continue
        return raw  # type: ignore[return-value]


def ask_optional(prompt: str) -> str:
    """선택 입력 (빈 값 허용)."""
    try:
        return input(f"{prompt} (선택, 엔터 스킵): ").strip()
    except EOFError:
        return ""


def confirm(prompt: str) -> bool:
    """y/n 확인."""
    while True:
        ans = input(f"{prompt} [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no", ""):
            return False
        print("[오류] y 또는 n을 입력하세요.")

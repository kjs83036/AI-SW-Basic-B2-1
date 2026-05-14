"""공통 관심사 데코레이터: handle_errors, log_run, timed."""
from __future__ import annotations

import functools
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from budget_app.errors import BudgetAppError

F = TypeVar("F", bound=Callable)

_log_path: Path | None = None


def set_log_path(path: Path) -> None:
    global _log_path
    _log_path = path


def _write_log(message: str) -> None:
    if _log_path is None:
        return
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with _log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
    except OSError:
        pass


def handle_errors(func: F) -> F:
    """도메인 예외 → [오류]/[힌트] 출력 후 exit(1). 스택트레이스 금지."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e}")
            if e.hint:
                print(f"[힌트] {e.hint}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[취소]")
            sys.exit(0)
        except Exception as e:
            print(f"[오류] 예상치 못한 오류가 발생했습니다: {type(e).__name__}: {e}")
            sys.exit(1)
    return wrapper  # type: ignore[return-value]


def log_run(func: F) -> F:
    """실행 시작/종료를 app.log에 기록한다."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_log(f"[{ts}] START {func.__name__}")
        try:
            result = func(*args, **kwargs)
            ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_log(f"[{ts2}] OK    {func.__name__}")
            return result
        except SystemExit as e:
            ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_log(f"[{ts2}] EXIT  {func.__name__} code={e.code}")
            raise
        except Exception as e:
            ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_log(f"[{ts2}] ERR   {func.__name__} {type(e).__name__}: {e}")
            raise
    return wrapper  # type: ignore[return-value]


def timed(func: F) -> F:
    """소요 시간을 측정해 로그에 기록한다."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            _write_log(f"[TIMED] {func.__name__} {elapsed:.3f}s")
    return wrapper  # type: ignore[return-value]

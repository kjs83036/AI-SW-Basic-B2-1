# 파일 기반 가계부 콘솔 프로그램

## 개요

Python 3.10 이상, 표준 라이브러리만 사용하는 파일 기반 가계부 콘솔 프로그램이다. JSONL 형식으로 거래/카테고리/예산 데이터를 영구 저장하며 add/list/search/summary/budget/category/update/delete/import/export 10가지 명령을 제공한다.

## 실행 방법

```bash
python -m budget_app <명령> [옵션]
python -m budget_app --help
```

## 저장 파일 위치 및 형식

기본 위치: `./data/`  
변경: `--data-dir <폴더경로>` 옵션 사용

| 파일 | 형식 | 설명 |
|------|------|------|
| data/transactions.jsonl | JSONL | 거래 내역 (줄당 JSON 1건) |
| data/categories.jsonl | JSONL | 카테고리 목록 |
| data/budgets.jsonl | JSONL | 월별 예산 |

## 주요 명령 예시

```bash
# 거래 추가 (대화형)
python -m budget_app add

# 목록 조회 (최신순 10건)
python -m budget_app list --limit 10

# 검색
python -m budget_app search --from 2024-01-01 --to 2024-01-31
python -m budget_app search --category food --type expense
python -m budget_app search --q 점심 --tag meal

# 월별 요약
python -m budget_app summary --month 2024-01 --top 3

# 예산 설정
python -m budget_app budget set --month 2024-01 --amount 500000

# 카테고리 관리
python -m budget_app category list
python -m budget_app category add
python -m budget_app category remove

# 거래 수정 (옵션 기반)
python -m budget_app update --id TX-000001 --memo "수정된 메모" --amount 20000

# 거래 삭제
python -m budget_app delete --id TX-000001

# CSV 내보내기 (--month 또는 --from/--to 중 하나 이상 필수)
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31

# CSV 가져오기
python -m budget_app import --from import.csv

# 데이터 저장 위치 변경
python -m budget_app --data-dir /path/to/mydata list
```

## import/export CSV 스키마

```
UTF-8, 첫 줄은 헤더
```

| column | required | 설명 |
|--------|----------|------|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 (import 시 미등록이면 자동 추가) |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

## 파일

- `budget_app/models.py` — Transaction, Budget dataclass
- `budget_app/repository.py` — TransactionRepository, CategoryStore, BudgetStore
- `budget_app/service.py` — BudgetService + handle_errors 데코레이터
- `budget_app/__main__.py` — argparse CLI 진입점
- `architecture.md` — 모듈/클래스/실행흐름 mermaid 구조도
- `EXPLANATION.md` — 코드리뷰 수준 통합 설명 (설계 의도 + PDF 제약 매핑)
- `MANUAL_VERIFICATION.md` — 수동 검증 가이드
- `README.md` — 본 문서
- `review/` — **초보자용 라인별 코드 학습 문서** (비유·배경지식 포함, 함수 하나씩 워크스루)
  - `review/README.md` — 읽는 순서 + 새 문법 사전
  - `review/models.md` — Transaction, Budget 클래스 해설
  - `review/repository.md` — 파일 I/O 3개 저장소 클래스 해설
  - `review/service.md` — 데코레이터·검증·명령 처리 해설
  - `review/__main__.md` — argparse CLI 진입점 해설

## 결과 요약

Python 표준 라이브러리만 사용하여 10개 필수 기능 모두 구현. JSONL 3개 파일 영구 저장, 제너레이터 스트리밍, handle_errors 데코레이터 적용, 오류 시 스택트레이스 없이 [오류]+[힌트] 출력 및 exit code 1 종료.

# 파일 기반 가계부 콘솔 프로그램

AI/SW 기초 (AI/SW Basic) — Python & Git Advanced 과제

## 실행 환경

- Python 3.10 이상
- 외부 라이브러리 불필요 (표준 라이브러리만 사용)

## 실행 방법

```bash
python -m budget_app <command> [options]
```

데이터 저장 위치 변경:
```bash
python -m budget_app --data-dir ./mydata <command>
```

---

## 저장 파일 위치 및 형식

| 파일 | 경로 | 설명 |
|---|---|---|
| 거래 내역 | `./data/transactions.csv` | 모든 수입/지출 거래 |
| 카테고리 | `./data/categories.csv` | 카테고리 목록 |
| 예산 | `./data/budgets.csv` | 월별 예산 설정 |
| 실행 로그 | `./data/app.log` | 명령 실행 이력 |

- 저장 포맷: **CSV (UTF-8, 헤더 포함)**
- 쓰기 방식: tmp 파일 생성 후 `os.replace` 원자적 교체
- 읽기 방식: `csv.DictReader` yield 기반 스트리밍 (파일 전체 메모리 로드 없음)

### 내부 저장 스키마 (transactions.csv)

| column | required | 설명 |
|---|---|---|
| id | Y | TX-000001 형식 자동 발급 |
| type | Y | income / expense |
| date | Y | YYYY-MM-DD |
| amount | Y | 양수 정수 |
| category | Y | 등록된 카테고리 |
| memo | N | 선택 메모 |
| tags | N | 세미콜론(;) 구분 태그 |

---

## 주요 명령 예시

### 거래 추가 (대화형)
```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
[카테고리 목록] food, transport, rent, salary, ...
카테고리: food
금액(양수): 15000
메모 (선택, 엔터 스킵): 점심
태그(쉼표로 구분, 없으면 엔터) (선택, 엔터 스킵): meal
[저장 완료] id=TX-000001
```

### 거래 목록 조회
```
$ python -m budget_app list --limit 5
TX-000001 | 2024-01-15 | expense | food | 15000 | 점심 | meal
```

### 거래 검색
```
$ python -m budget_app search --from 2024-01-01 --to 2024-01-31 --type expense
$ python -m budget_app search --category food
$ python -m budget_app search -q 점심
$ python -m budget_app search --tag meal
```

### 월별 요약
```
$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3,000,000원
총 지출: 215,000원
잔액: 2,785,000원
예산: 500,000원 (사용률 43.0%)

지출 TOP 3
1) rent 150,000원
2) food 45,000원
3) transport 20,000원
```

### 예산 설정
```
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500,000원
```

### 거래 수정 (옵션 기반)
```
$ python -m budget_app update --id TX-000001 --amount 17000 --memo 수정된메모
[수정 완료] id=TX-000001
```

### 거래 삭제
```
$ python -m budget_app delete --id TX-000001
[삭제 완료] id=TX-000001
```

### 카테고리 관리
```
$ python -m budget_app category list
$ python -m budget_app category add coffee
$ python -m budget_app category remove coffee
```

### CSV 내보내기 / 가져오기
```
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```

### 데이터 백업
```
$ python -m budget_app backup
[백업 완료] data/backup_20240115_120000
```

---

## import/export CSV 스키마

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

- 공통: UTF-8, 헤더 포함
- 잘못된 행은 자동 skip (skipped 카운트에 반영)

---

## 아키텍처

```
CLI (cli.py + commands.py)
  └─ Service 계층 (services/)
       └─ Repository 계층 (repositories/)
            └─ Model 계층 (models/)
                 └─ data/*.csv
```

### 모듈 구조

| 모듈 | 책임 |
|---|---|
| `models/` | dataclass (Transaction, Category, Budget) + CSV 직렬화 |
| `repositories/` | CSV 파일 I/O (스트리밍 읽기, 원자적 쓰기) |
| `services/` | 비즈니스 로직, 입력 검증, 집계 |
| `cli.py` | argparse 라우팅, --help |
| `commands.py` | CLI 명령 핸들러 (데코레이터 적용) |
| `decorators.py` | @handle_errors, @log_run, @timed |
| `prompts.py` | 대화형 입력 헬퍼 |
| `errors.py` | 도메인 예외 클래스 |
| `config.py` | 경로 상수, 기본값 |

---

## 오류 처리

- 스택트레이스 미출력
- `[오류] 원인`, `[힌트] 해결 방법` 형식으로 출력
- 오류 종료 시 exit code = 1, 정상 종료 시 exit code = 0

from dataclasses import dataclass


@dataclass
class Transaction:
    id: str
    type: str        # income | expense
    date: str        # YYYY-MM-DD (정규화된 형식으로 저장)
    amount: int      # 양수 정수
    category: str
    memo: str = ""
    tags: str = ""   # 쉼표(,) 구분 문자열


@dataclass
class Budget:
    month: str   # YYYY-MM
    amount: int  # 양수 정수

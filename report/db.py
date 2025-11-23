# 코드 작성일 25/11/21
# DB에서 소비 내역 읽어오기(예시)
# 차후 수정 예정
# db.py
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

DB_PATH = "openwallet.db"  # 실제 경로에 맞게 변경


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_transactions_from_db(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    DB에서 특정 사용자(user_id)의 거래 내역 조회.
    테이블/컬럼 이름은 예시이므로 실제 스키마에 맞게 수정하면 됩니다.

    예시 테이블 스키마:
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT,
        merchant TEXT,
        amount INTEGER,
        suggested_category TEXT,
        raw_json TEXT  -- OCR에서 나온 원본 JSON (옵션)
    );
    """
    query = """
        SELECT date, merchant, amount, suggested_category
        FROM transactions
        WHERE user_id = ?
    """
    params: list[Any] = [user_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    with get_connection() as conn:
        cur = conn.cursor()
        rows = cur.execute(query, params).fetchall()

    return [dict(row) for row in rows]

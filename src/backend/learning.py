# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection
import pandas as pd

def get_word_batch(start: int = 0, limit: int = 100, order_by: str = "word_id") -> pd.DataFrame:
    conn = get_db_connection()

    # 安全な並び替えカラムの制限
    if order_by not in ("word_id", "word"):
        order_by = "word_id"

    # 明示的なカラム指定で安全に
    order_column = "w.word_id" if order_by == "word_id" else "w.word"

    df = pd.read_sql_query(
        f"""
        SELECT w.word_id, w.word, m.meaning, m.part_of_speech, m.category
        FROM words w
        JOIN meanings m ON w.word_id = m.word_id
        ORDER BY {order_column} COLLATE NOCASE
        LIMIT ? OFFSET ?
        """,
        conn,
        params=(limit, start)
    )
    conn.close()
    return df
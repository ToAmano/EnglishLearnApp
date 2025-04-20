# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection
import pandas as pd

def get_word_batch(start: int = 0, limit: int = 100) -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql_query(
        """
        SELECT w.word_id, w.word, m.meaning, m.part_of_speech, m.category
        FROM words w
        JOIN meanings m ON w.word_id = m.word_id
        ORDER BY w.word_id
        LIMIT ? OFFSET ?
        """,
        conn,
        params=(limit, start)
    )
    conn.close()
    return df
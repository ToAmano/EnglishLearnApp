# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection

def get_explanation(word_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT explanation FROM word_explanations WHERE word_id = ?", (word_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
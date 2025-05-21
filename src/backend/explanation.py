# -*- coding: utf-8 -*-
from typing import Any

from backend.core.db_core import get_db_connection


def get_explanation(word_id: int) -> Any | None:
    """extract explanation from word_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT explanation FROM word_explanations WHERE word_id = ?", (word_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

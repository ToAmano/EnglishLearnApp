# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection


def get_search_count(word_id: int) -> int:
    """Get the search count for a given word_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM search_logs WHERE word_id = ?", (word_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def increment_search_count(word_id: int) -> None:
    """Increment the search count for a given word_id."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO search_logs (word_id, count) VALUES (?, 1)
        ON CONFLICT(word_id) DO UPDATE SET count = count + 1
    """,
        (word_id,),
    )
    conn.commit()
    conn.close()

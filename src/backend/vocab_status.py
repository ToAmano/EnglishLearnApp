# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection


def get_vocab_status(word_id: int) -> str:
    """Get the vocabulary status for a given word_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM vocab_status WHERE word_id = ?", (word_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "unknown"  # 初期値として 'unknown'


def set_vocab_status(word_id: int, status: str) -> None:
    """Set the vocabulary status for a given word_id."""
    print(f"Updated vocab status for word_id {word_id} to {status}")
    assert status in ("unknown", "passive", "active"), "Invalid status"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vocab_status (word_id, status)
        VALUES (?, ?)
        ON CONFLICT(word_id) DO UPDATE SET status=excluded.status
    """,
        (word_id, status),
    )
    conn.commit()
    conn.close()
    print(f"Updated vocab status for word_id {word_id} to {status}")

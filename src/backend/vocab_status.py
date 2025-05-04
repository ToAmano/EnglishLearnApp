# -*- coding: utf-8 -*-
from backend.core.db_core import get_db_connection,get_user_db_connection


def get_vocab_status(word: str) -> str:
    """Get the vocabulary status for a given word_id."""
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM vocab_status WHERE word = ?", (word,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "unknown"  # 初期値として 'unknown'


def set_vocab_status(word: str, status: str) -> None:
    """Set the vocabulary status for a given word_id."""
    print(f"Updated vocab status for word {word} to {status}")
    assert status in ("unknown", "passive", "active"), "Invalid status"
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vocab_status (word, status)
        VALUES (?, ?)
        ON CONFLICT(word) DO UPDATE SET status=excluded.status
    """,
        (word, status),
    )
    conn.commit()
    conn.close()
    print(f"Updated vocab status for word_id {word} to {status}")

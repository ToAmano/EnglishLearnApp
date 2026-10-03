"""アカウント別の語彙習得状態。"""

from contextlib import closing

from backend.core.db_core import get_user_db_connection


def get_vocab_status(word: str, user_id: str) -> str:
    with closing(get_user_db_connection()) as conn:
        row = conn.execute(
            "SELECT status FROM user_vocab_status WHERE user_id = ? AND word = ?",
            (user_id, word),
        ).fetchone()
    return str(row["status"]) if row else "unknown"


def set_vocab_status(word: str, status: str, user_id: str) -> None:
    if status not in ("unknown", "passive", "active"):
        raise ValueError("習得状態が不正です。")
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.execute(
                "INSERT INTO user_vocab_status(user_id, word, status) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, word) DO UPDATE SET status = excluded.status",
                (user_id, word, status),
            )

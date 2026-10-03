"""既存の単一ユーザーデータを保持し、アカウント別の保存先を追加する。"""

from contextlib import closing

from backend.core.db_core import get_user_db_connection


def initialize_user_schema() -> None:
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    UNIQUE(provider, subject)
                );
                CREATE TABLE IF NOT EXISTS user_favorites (
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    word TEXT NOT NULL,
                    PRIMARY KEY(user_id, word)
                );
                CREATE TABLE IF NOT EXISTS user_vocab_status (
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    word TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('unknown', 'passive', 'active')),
                    PRIMARY KEY(user_id, word)
                );
                """
            )

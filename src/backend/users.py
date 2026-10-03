"""Googleの永続subjectをアプリ内部のユーザーIDへ対応付ける。"""

from contextlib import closing
from uuid import uuid4

from backend.core.db_core import get_user_db_connection
from backend.core.user_schema import initialize_user_schema


def get_or_create_google_user(subject: str) -> str:
    if not subject.strip():
        raise ValueError("Googleのユーザー識別子が必要です。")
    initialize_user_schema()
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.execute(
                "INSERT INTO users(user_id, provider, subject) VALUES (?, 'google', ?) "
                "ON CONFLICT(provider, subject) DO NOTHING",
                (str(uuid4()), subject),
            )
            row = conn.execute(
                "SELECT user_id FROM users WHERE provider = 'google' AND subject = ?",
                (subject,),
            ).fetchone()
    return str(row["user_id"])

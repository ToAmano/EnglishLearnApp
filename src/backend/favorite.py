"""アカウント別のお気に入り。旧favoritesは後日の引き継ぎ用に保持する。"""

from contextlib import closing

from backend.core.db_core import get_user_db_connection


def is_favorited(word: str, user_id: str) -> bool:
    with closing(get_user_db_connection()) as conn:
        return (
            conn.execute(
                "SELECT 1 FROM user_favorites WHERE user_id = ? AND word = ?",
                (user_id, word),
            ).fetchone()
            is not None
        )


def toggle_favorite(word: str, user_id: str) -> None:
    with closing(get_user_db_connection()) as conn:
        with conn:
            # 読み取りと更新を同じ書き込みトランザクションにする。
            conn.execute("BEGIN IMMEDIATE")
            deleted = conn.execute(
                "DELETE FROM user_favorites WHERE user_id = ? AND word = ?",
                (user_id, word),
            )
            if not deleted.rowcount:
                conn.execute(
                    "INSERT INTO user_favorites(user_id, word) VALUES (?, ?)",
                    (user_id, word),
                )


def get_favorites_words(user_id: str) -> list[str]:
    with closing(get_user_db_connection()) as conn:
        rows = conn.execute(
            "SELECT word FROM user_favorites WHERE user_id = ? ORDER BY word",
            (user_id,),
        ).fetchall()
    return [str(row["word"]) for row in rows]

from typing import List

from backend.core.db_core import get_user_db_connection


def is_favorited(word: str) -> bool:
    """Check if the word is favorited"""
    conn = get_user_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM favorites WHERE word = ?", (word,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def toggle_favorite(word: str) -> None:
    """Change the state of favorited for the word"""
    conn = get_user_db_connection()
    cur = conn.cursor()
    if is_favorited(word):
        cur.execute("DELETE FROM favorites WHERE word = ?", (word,))
    else:
        cur.execute("INSERT INTO favorites (word) VALUES (?)", (word,))
    conn.commit()
    conn.close()


def get_favorites_words() -> List[str]:
    """Get all the favorited words"""
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM favorites")
    favorite_words: List[str] = [row[0] for row in cursor.fetchall()]  # list of words
    conn.close()
    return favorite_words

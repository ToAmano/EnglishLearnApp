import os
import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Any

# "src/" directory, resolved from this file's own location rather than the
# current working directory. Used as the base for the default database
# paths below so the app finds the databases whether it is launched from
# the repository root or from inside src/.
_SRC_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_WORDS_DB_PATH = str(_SRC_DIR / "database" / "words.db")
_DEFAULT_USER_DB_PATH = str(_SRC_DIR / "database" / "user.db")


def get_db_connection() -> Connection:
    """Get a database connection."""
    db_path: str = os.getenv("WORDS_DB_PATH", _DEFAULT_WORDS_DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_db_connection() -> Connection:
    """Get a user database connection."""
    db_path: str = os.getenv("USER_DB_PATH", _DEFAULT_USER_DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_word_from_wordid(word_id: int) -> Any | None:
    """Get the word from the database using word_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words WHERE word_id=?", (word_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_wordid_from_word(word: str) -> int:
    """Get the word_id from the given word"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word_id FROM words WHERE word=?", (word,))
    word_id_row = cursor.fetchone()
    conn.close()
    if not word_id_row:  # return empty df if not found
        print("word not found")
        return 0
    word_id: int = word_id_row[0]
    print(f"search word {word} :: word_id {word_id}")
    return word_id

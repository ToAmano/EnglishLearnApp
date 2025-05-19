import sqlite3


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect("database/words.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_user_db_connection():
    """Get a user database connection."""
    conn = sqlite3.connect("database/user.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_word_from_wordid(word_id: int) -> str:
    """Get the word from the database using word_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words WHERE word_id=?", (word_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_wordid_from_word(word: str) -> int:
    """単語検索"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word_id FROM words WHERE word=?", (word,))
    word_id_row = cursor.fetchone()
    conn.close()
    if not word_id_row:  # return empty df if not found
        print("word not found")
        return 0
    word_id = word_id_row[0]
    print(f"search word {word} :: word_id {word_id}")
    return word_id

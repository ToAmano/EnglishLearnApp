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


def get_word_from_wordid(word_id):
    """Get the word from the database using word_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words WHERE word_id=?", (word_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

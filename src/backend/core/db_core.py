import sqlite3

def get_db_connection():
    conn = sqlite3.connect("database/words.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_word_from_wordid(word_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words WHERE word_id=?", (word_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

import sqlite3


def init_db():
    conn = sqlite3.connect("words.db")
    cursor = conn.cursor()

    # Table for words
    cursor.execute(
        """
    CREATE TABLE words (
        word_id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        source TEXT 
    );
    """
    )
    
    # Table for explanation
    cursor.execute(
        """
    CREATE TABLE word_explanations (
        word_id INTEGER PRIMARY KEY,
        explanation TEXT NOT NULL,
        FOREIGN KEY (word_id) REFERENCES words(word_id)
    );
    """
    )

    
    # Table for meanings
    cursor.execute(
        """
    CREATE TABLE meanings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        meaning TEXT NOT NULL,
        part_of_speech TEXT,
        category TEXT,
        FOREIGN KEY (word_id) REFERENCES words(word_id)
    );
    """
    )

    # Table for examples
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        example TEXT NOT NULL,
        audio_path TEXT,
        FOREIGN KEY (word_id) REFERENCES words (word_id)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (word_id) REFERENCES words (word_id)
    );
    """
    )

    # table for stems
    cursor.execute(
        """
        CREATE TABLE stems (
        stem_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stem TEXT UNIQUE NOT NULL
        );
    """
    )

    # table for derivative words
    cursor.execute(
        """
    CREATE TABLE derived_words (
        word_id INTEGER NOT NULL,
        stem_id INTEGER NOT NULL,
        FOREIGN KEY (word_id) REFERENCES words(word_id),
        FOREIGN KEY (stem_id) REFERENCES stems(stem_id),
        PRIMARY KEY (word_id, stem_id)
    );
    """
    )

    # table for synonyms
    cursor.execute(
        """
    CREATE TABLE synonyms (
        word_id_1 INTEGER NOT NULL,
        word_id_2 INTEGER NOT NULL,
        FOREIGN KEY (word_id_1) REFERENCES words(word_id),
        FOREIGN KEY (word_id_2) REFERENCES words(word_id),
        PRIMARY KEY (word_id_1, word_id_2)
    );
    """
    )

    # table for word search logs
    cursor.execute(
        """
    CREATE TABLE search_logs (
        word_id INTEGER NOT NULL,
        count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (word_id) REFERENCES words(word_id),
        PRIMARY KEY (word_id)
    );
    """
    )

    # table for word status (unknown, passive, active)
    cursor.execute(
        """
    CREATE TABLE vocab_status (
        word_id INTEGER PRIMARY KEY,
        status TEXT NOT NULL CHECK (status IN ('unknown', 'passive', 'active')),
        FOREIGN KEY (word_id) REFERENCES words(word_id)
    );
    """
    )
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("データベースを初期化しました。")

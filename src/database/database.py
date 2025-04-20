import sqlite3


def init_db():
    conn = sqlite3.connect("words.db")
    cursor = conn.cursor()

    # Table for words
    cursor.execute(
        """
    CREATE TABLE words (
        word_id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE
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


def insert_sample_data():
    conn = sqlite3.connect("words.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO words (word_id, word) VALUES (1, 'bright')")
    cursor.execute("INSERT INTO words (word_id, word) VALUES (2, 'dark')")
    cursor.execute("INSERT INTO words (word_id, word) VALUES (3, 'brightness')")
    cursor.execute("INSERT INTO words (word_id, word) VALUES (4, 'brighten')")
    cursor.execute("INSERT INTO words (word_id, word) VALUES (5, 'brightly')")

    cursor.execute(
        "INSERT INTO meanings (word_id, meaning, part_of_speech, category) VALUES (1, '輝いている', 'adj', '天気')"
    )
    cursor.execute(
        "INSERT INTO meanings (word_id, meaning, part_of_speech, category) VALUES (1, '頭が良い', 'adj', '性格')"
    )
    cursor.execute(
        "INSERT INTO meanings (word_id, meaning, part_of_speech, category) VALUES (2, '暗い', 'adj', '天気')"
    )
    # brightness: 明るさ（名詞）
    cursor.execute(
        """
        INSERT INTO meanings (word_id, meaning, part_of_speech, category)
        VALUES (3, '明るさ', 'noun', '天気')
    """
    )

    # brighten: 明るくする／なる（動詞）
    cursor.execute(
        """
        INSERT INTO meanings (word_id, meaning, part_of_speech, category)
        VALUES (4, '明るくする', 'verb', '天気')
    """
    )

    # brightly: 明るく（副詞）
    cursor.execute(
        """
        INSERT INTO meanings (word_id, meaning, part_of_speech, category)
        VALUES (5, '明るく', 'adverb', '天気')
    """
    )

    cursor.execute(
        "INSERT INTO examples (word_id, example, audio_path) VALUES (1, 'The sun is bright today.', 'audio/bright1.mp3')"
    )
    cursor.execute(
        "INSERT INTO examples (word_id, example, audio_path) VALUES (2, 'The room is dark.', 'audio/dark1.mp3')"
    )

    cursor.execute("INSERT INTO stems (stem) VALUES ('bright');")
    derived_words = ["bright", "brightness", "brighten", "brightly"]

    cursor.execute("SELECT stem_id FROM stems WHERE stem = ?", ("bright",))
    stem_id = cursor.fetchone()[0]

    for word in derived_words:
        cursor.execute("SELECT word_id FROM words WHERE word = ?", (word,))
        word_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT OR IGNORE INTO derived_words (word_id, stem_id) VALUES (?, ?)",
            (word_id, stem_id),
        )

    # 類義語の登録: bright と brightness
    cursor.execute(
        "INSERT OR IGNORE INTO synonyms (word_id_1, word_id_2) VALUES (?, ?)", (1, 3)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO synonyms (word_id_1, word_id_2) VALUES (?, ?)", (3, 1)
    )  # 双方向

    for word_id in range(1, 6):
        # init examples by empty string
        cursor.execute(
            "INSERT OR IGNORE INTO examples (word_id, example) VALUES (?, ?)",
            (word_id, ""),
        )

        # init stems by empty string
        cursor.execute(
            "INSERT OR IGNORE INTO stems (stem_id, stem) VALUES (?, ?)", (word_id, "")
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    insert_sample_data()
    print("データベースを初期化しました。")

import sqlite3
import os

def insert_sample_data():
    if not os.path.exists("words.db"):
        raise FileNotFoundError("Database not found.")
    # init database
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
        
        # init exlanations by sample text
        cursor.execute(
            "INSERT OR IGNORE INTO word_explanations (word_id, explanation) VALUES (?, ?)",
            (word_id, "This is a sample explanation."),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    insert_sample_data()
    print("データベースを初期化しました。")

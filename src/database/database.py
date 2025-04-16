import sqlite3

def init_db():
    conn = sqlite3.connect("words.db")
    cursor = conn.cursor()

    # Table for words
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_number INTEGER NOT NULL,
        word TEXT NOT NULL,
        meaning TEXT NOT NULL,
        part_of_speech TEXT,
        category TEXT        
    );
    ''')

    # Table for examples
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_number INTEGER NOT NULL,
        example TEXT NOT NULL,
        audio_path TEXT,
        FOREIGN KEY (word_number) REFERENCES words (word_number)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_number INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (word_number) REFERENCES words (word_number)
    );
    ''')

    conn.commit()
    conn.close()

def insert_sample_data():
    conn = sqlite3.connect("words.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO words (word_number, word, meaning, part_of_speech, category) VALUES (1, 'bright', '輝いている', 'adj', '天気')")
    cursor.execute("INSERT INTO words (word_number, word, meaning, part_of_speech, category) VALUES (1, 'bright', '頭が良い', 'adj', '性格')")
    cursor.execute("INSERT INTO words (word_number, word, meaning, part_of_speech, category) VALUES (2, 'dark', '暗い', 'adj', '天気')")


    cursor.execute("INSERT INTO examples (word_number, example, audio_path) VALUES (1, 'The sun is bright today.', 'audio/bright1.mp3')")
    cursor.execute("INSERT INTO examples (word_number, example, audio_path) VALUES (2, 'The room is dark.', 'audio/dark1.mp3')")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    insert_sample_data()
    print("データベースを初期化しました。")
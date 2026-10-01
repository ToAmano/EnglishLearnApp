import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "instance/words.db"))
WORD_DATA_DIR = Path("src/data/word_data")


def get_db_connection(db_path=DATABASE_PATH):
    """データベース接続を確立し、カーソルを返す"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # カラム名でアクセスできるようにする
    return conn


def init_db(conn):
    """データベーステーブルを初期化（存在しない場合のみ作成）"""
    cursor = conn.cursor()

    # --- マスターテーブル ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            word TEXT NOT NULL,
            original_word_id INTEGER,
            explanation TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stem TEXT UNIQUE NOT NULL
        )
    """
    )

    # --- 単語属性テーブル (wordsテーブルへの関連) ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_meanings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_uuid TEXT NOT NULL,
            part_of_speech TEXT,
            meaning TEXT NOT NULL,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_word_meanings_word_uuid ON word_meanings(word_uuid)"
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_uuid TEXT NOT NULL,
            example TEXT NOT NULL,
            translation TEXT,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_word_examples_word_uuid ON word_examples(word_uuid)"
    )

    # --- 関係テーブル ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_source_links (
            word_uuid TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            PRIMARY KEY (word_uuid, source_id),
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_derivations (
            word_uuid TEXT NOT NULL,
            stem_id INTEGER NOT NULL,
            PRIMARY KEY (word_uuid, stem_id),
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE,
            FOREIGN KEY (stem_id) REFERENCES stems(id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_synonyms (
            word_uuid_1 TEXT NOT NULL,
            word_uuid_2 TEXT NOT NULL,
            PRIMARY KEY (word_uuid_1, word_uuid_2),
            FOREIGN KEY (word_uuid_1) REFERENCES words(uuid) ON DELETE CASCADE,
            FOREIGN KEY (word_uuid_2) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )

    # --- ユーザーデータテーブル ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_favorites (
            user_id INTEGER NOT NULL,
            word_uuid TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, word_uuid),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_favorites_word_uuid ON user_favorites(word_uuid)"
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_vocab_status (
            user_id INTEGER NOT NULL,
            word_uuid TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('passive', 'active')),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, word_uuid),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_vocab_status_word_uuid ON user_vocab_status(word_uuid)"
    )

    # --- ログ/統計テーブル ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_search_counts (
            user_id INTEGER NOT NULL,
            word_uuid TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id, word_uuid),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_search_counts_word_uuid ON user_search_counts(word_uuid)"
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS word_global_search_counts (
            word_uuid TEXT PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (word_uuid) REFERENCES words(uuid) ON DELETE CASCADE
        )
    """
    )

    conn.commit()

import os  # Add this import
import sqlite3
import uuid  # Added this import
from pathlib import Path

import pytest
from typer.testing import CliRunner

# Assuming the main Typer app is located at src/data_pipeline/main.py
# and the commands are now functions directly registered to it.
from src.data_pipeline.db_manager import (
    DATABASE_PATH,
    WORD_DATA_DIR,
    get_db_connection,
    init_db,
)
from src.data_pipeline.main import app

runner = CliRunner()

# Define a temporary database path for testing
TEST_DATABASE_PATH = Path("instance/test_words.db")
# Define a temporary word data directory for testing CSVs
TEST_WORD_DATA_DIR = Path("src/data/word_data/temp_test_csvs")


@pytest.fixture(name="db_conn")
def setup_test_db():
    """
    テスト用データベースをセットアップし、テスト後にクリーンアップするフィクスチャ。
    """
    # Set the DATABASE_PATH environment variable for the command execution
    original_db_path_env = os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = str(TEST_DATABASE_PATH)

    # テスト前に既存のテストDBを削除
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink(missing_ok=True)  # Use missing_ok for robustness

    conn = get_db_connection(db_path=TEST_DATABASE_PATH)
    init_db(conn)  # スキーマを初期化
    yield conn
    conn.close()
    # テスト後にDBファイルを削除
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink(missing_ok=True)

    # Restore original environment variable
    if original_db_path_env is not None:
        os.environ["DATABASE_PATH"] = original_db_path_env
    else:
        del os.environ["DATABASE_PATH"]


@pytest.fixture(name="test_csv_dir")
def setup_test_csv_dir():
    """
    テスト用CSVディレクトリをセットアップし、テスト後にクリーンアップするフィクスチャ。
    """
    if TEST_WORD_DATA_DIR.exists():
        for f in TEST_WORD_DATA_DIR.iterdir():
            f.unlink()
        TEST_WORD_DATA_DIR.rmdir()
    TEST_WORD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield TEST_WORD_DATA_DIR
    if TEST_WORD_DATA_DIR.exists():
        for f in TEST_WORD_DATA_DIR.iterdir():
            f.unlink()
        TEST_WORD_DATA_DIR.rmdir()


def test_consolidate_words_adds_word_from_csv(db_conn, test_csv_dir):
    """
    consolidate-wordsコマンドがCSVから単語を正しくデータベースに追加することを確認
    """
    # テスト用CSVファイルを作成
    csv_content = "word_id,word,source\n1,testword,TestBook"
    csv_file = test_csv_dir / "test.csv"
    csv_file.write_text(csv_content)

    # コマンドを実行
    result = runner.invoke(app, ["consolidate-words", "--data-dir", str(test_csv_dir)])

    # 標準出力にエラーがないことを確認
    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "単語データの統合を開始します..." in result.stdout
    assert "単語データの統合が完了しました。" in result.stdout

    # データベースに単語が追加されたことを確認
    cursor = db_conn.cursor()
    cursor.execute("SELECT word, original_word_id FROM words WHERE word = 'testword'")
    word_entry = cursor.fetchone()
    assert word_entry is not None
    assert word_entry["word"] == "testword"
    assert word_entry["original_word_id"] == 1

    # ソースが追加されたことを確認
    cursor.execute("SELECT name FROM sources WHERE name = 'TestBook'")
    source_entry = cursor.fetchone()
    assert source_entry is not None
    assert source_entry["name"] == "TestBook"

    # word_source_linksが正しく作成されたことを確認
    cursor.execute(
        """
        SELECT w.word, s.name FROM word_source_links wsl
        JOIN words w ON wsl.word_uuid = w.uuid
        JOIN sources s ON wsl.source_id = s.id
        WHERE w.word = 'testword' AND s.name = 'TestBook'
        """
    )
    link_entry = cursor.fetchone()
    assert link_entry is not None
    assert link_entry["word"] == "testword"
    assert link_entry["name"] == "TestBook"


def test_consolidate_words_updates_existing_word(db_conn, test_csv_dir):
    """
    consolidate-wordsコマンドが既存の単語を更新することを確認
    """
    # 事前に単語をDBに追加
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), "existingword", 0, True),
    )
    db_conn.commit()

    # テスト用CSVファイルを作成
    csv_content = "word_id,word,source\n1,existingword,TestBook"
    csv_file = test_csv_dir / "test.csv"
    csv_file.write_text(csv_content)

    # コマンドを実行
    result = runner.invoke(app, ["consolidate-words", "--data-dir", str(test_csv_dir)])

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"

    # 単語が重複せず存在することを確認 (UUIDは変わらず)
    cursor.execute("SELECT COUNT(*) FROM words WHERE word = 'existingword'")
    assert cursor.fetchone()[0] == 1


def test_consolidate_words_deactivates_missing_word(db_conn, test_csv_dir):
    """
    consolidate-wordsコマンドがCSVに存在しない単語を非アクティブ化することを確認
    """
    # 事前に単語をDBに追加
    initial_uuid = str(uuid.uuid4())
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (initial_uuid, "missingword", 0, True),
    )
    db_conn.commit()

    # コマンドを実行 (空のCSVディレクトリで)
    result = runner.invoke(
        app, ["consolidate-words", "--data-dir", str(test_csv_dir)]
    )  # test_csv_dirは空

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert (
        "単語 'missingword' がCSVから削除されたため、非アクティブ化します。"
        in result.stdout
    )

    # 単語が非アクティブ化されたことを確認
    cursor.execute("SELECT is_active FROM words WHERE word = 'missingword'")
    assert cursor.fetchone()["is_active"] == 0  # SQLiteではBOOLEANは0/1で表現


def test_consolidate_words_handles_empty_data_dir(db_conn, test_csv_dir):
    """
    consolidate-wordsコマンドが空のデータディレクトリを正しく処理することを確認
    """
    # 事前に単語をDBに追加
    initial_uuid = str(uuid.uuid4())
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (initial_uuid, "anotherword", 0, True),
    )
    db_conn.commit()

    # コマンドを実行 (test_csv_dirは空)
    result = runner.invoke(app, ["consolidate-words", "--data-dir", str(test_csv_dir)])

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert (
        "単語 'anotherword' がCSVから削除されたため、非アクティブ化します。"
        in result.stdout
    )

    # 単語が非アクティブ化されたことを確認
    cursor.execute("SELECT is_active FROM words WHERE word = 'anotherword'")
    assert cursor.fetchone()["is_active"] == 0


def test_check_spelling_finds_misspelled_word(db_conn, test_csv_dir):
    """
    check-spellingコマンドがスペルミスのある単語を検出することを確認
    """
    # テスト用CSVファイルを作成
    csv_content = "word_id,word,source\n1,aple,Book A"  # "aple" はスペルミス
    csv_file = test_csv_dir / "misspell.csv"
    csv_file.write_text(csv_content)

    # コマンドを実行
    result = runner.invoke(
        app, ["check-spelling", "--data-dir", str(test_csv_dir), "--lang", "en"]
    )

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "ファイル: misspell.csv" in result.stdout
    assert "'aple'" in result.stdout
    assert "修正候補:" in result.stdout  # Make assertion more robust
    assert "apple" in result.stdout  # Ensure 'apple' is among candidates
    assert "合計 1 件のスペルミスの可能性がある単語が見つかりました。" in result.stdout


def test_check_spelling_finds_no_misspelled_word(db_conn, test_csv_dir):
    """
    check-spellingコマンドがスペルミスのある単語を検出しないことを確認
    """
    # テスト用CSVファイルを作成
    csv_content = "word_id,word,source\n1,apple,Book A"  # "apple" は正しいスペル
    csv_file = test_csv_dir / "correct.csv"
    csv_file.write_text(csv_content)

    # コマンドを実行
    result = runner.invoke(
        app, ["check-spelling", "--data-dir", str(test_csv_dir), "--lang", "en"]
    )

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "スペルミスの可能性がある単語は見つかりませんでした。" in result.stdout


def test_curate_words_rename_success(db_conn):
    """
    curate-words renameコマンドが単語を正しくリネームすることを確認
    """
    # 事前に単語をDBに追加
    initial_uuid = str(uuid.uuid4())
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (initial_uuid, "oldword", 0, True),
    )
    db_conn.commit()

    # コマンドを実行
    result = runner.invoke(
        app, ["curate-words", "rename", "--from", "oldword", "--to", "newword"]
    )

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "成功: 単語 'oldword' を 'newword' にリネームしました。" in result.stdout

    # DBで単語がリネームされたことを確認
    cursor.execute("SELECT word FROM words WHERE uuid = ?", (initial_uuid,))
    word_entry = cursor.fetchone()
    assert word_entry is not None
    assert word_entry["word"] == "newword"

    # 古い単語が存在しないことを確認
    cursor.execute("SELECT word FROM words WHERE word = 'oldword'")
    assert cursor.fetchone() is None


def test_curate_words_rename_from_word_not_found(db_conn):
    """
    curate-words renameコマンドが、存在しない単語のリネームを拒否することを確認
    """
    result = runner.invoke(
        app, ["curate-words", "rename", "--from", "nonexistent", "--to", "newword"]
    )
    assert result.exit_code == 1
    assert (
        "エラー: 修正元の単語 'nonexistent' がデータベースに存在しません。"
        in result.output
    )  # Check output, not stderr


def test_curate_words_rename_to_word_already_exists(db_conn):
    """
    curate-words renameコマンドが、既存の単語へのリネームを拒否することを確認
    """
    # 事前に単語をDBに追加
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), "existingtarget", 0, True),
    )
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), "wordtorename", 0, True),
    )
    db_conn.commit()

    result = runner.invoke(
        app,
        ["curate-words", "rename", "--from", "wordtorename", "--to", "existingtarget"],
    )
    assert result.exit_code == 1
    assert (
        "エラー: 修正先の単語 'existingtarget' は既にデータベースに存在します。"
        in result.output
    )  # Check output, not stderr


# generate-explanations のテスト (generate_explanation_for_word をモック)
from unittest.mock import patch


@patch("src.data_pipeline.commands.explanation_gen.generate_explanation_for_word")
def test_generate_explanations_success(mock_generate_explanation, db_conn):
    """
    generate-explanationsコマンドが説明文を正しく生成・保存することを確認
    """
    mock_generate_explanation.return_value = "This is a test explanation."

    # 事前に説明文がない単語をDBに追加
    word_uuid = str(uuid.uuid4())
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, explanation, is_active) VALUES (?, ?, ?, ?, ?)",
        (word_uuid, "explainword", 0, "", True),  # explanationを空で初期化
    )
    db_conn.commit()

    # コマンドを実行
    result = runner.invoke(app, ["generate-explanations", "--limit", "1"])

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "説明文の生成を開始します..." in result.stdout
    assert "1件の新しい説明文をデータベースに保存しています..." in result.stdout
    assert "データベースの更新が完了しました。" in result.stdout
    mock_generate_explanation.assert_called_once_with("explainword")

    # DBに説明文が保存されたことを確認
    cursor.execute("SELECT explanation FROM words WHERE word = 'explainword'")
    assert cursor.fetchone()["explanation"] == "This is a test explanation."


@patch("src.data_pipeline.commands.explanation_gen.generate_explanation_for_word")
def test_generate_explanations_no_words_to_explain(mock_generate_explanation, db_conn):
    """
    generate-explanationsコマンドが説明文が不要な単語がない場合に正しく動作することを確認
    """
    # 事前にすべての単語に説明文があると仮定
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, explanation, is_active) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), "alreadyexplained", 0, "Already has explanation.", True),
    )
    db_conn.commit()

    result = runner.invoke(app, ["generate-explanations"])

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "説明文が未生成の単語はありませんでした。" in result.stdout
    mock_generate_explanation.assert_not_called()


# migrate-user-data のテスト
@pytest.fixture(name="old_user_db")
def setup_old_user_db():
    """
    古いユーザーDBをセットアップし、テスト後にクリーンアップするフィクスチャ。
    """
    OLD_DB_PATH = Path("instance/old_user.db")
    if OLD_DB_PATH.exists():
        OLD_DB_PATH.unlink(missing_ok=True)  # Use missing_ok for robustness

    conn = sqlite3.connect(OLD_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            word TEXT PRIMARY KEY
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocab_status (
            word TEXT PRIMARY KEY,
            status TEXT
        )
        """
    )
    cursor.execute("INSERT INTO favorites (word) VALUES (?)", ("favword",))
    cursor.execute(
        "INSERT INTO vocab_status (word, status) VALUES (?, ?)",
        ("statusword", "active"),
    )
    conn.commit()
    conn.close()
    yield OLD_DB_PATH
    if OLD_DB_PATH.exists():
        OLD_DB_PATH.unlink(missing_ok=True)


def test_migrate_user_data_success(db_conn, old_user_db):
    """
    migrate-user-dataコマンドが古いDBからユーザーデータを正しく移行することを確認
    """
    # 事前に新しいDBに単語を追加 (UUIDを生成)
    cursor = db_conn.cursor()
    fav_uuid = str(uuid.uuid4())
    status_uuid = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (fav_uuid, "favword", 0, True),
    )
    cursor.execute(
        "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
        (status_uuid, "statusword", 0, True),
    )
    db_conn.commit()

    # コマンドを実行
    result = runner.invoke(
        app, ["migrate-user-data", "--old-db-path", str(old_user_db)]
    )

    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}: {result.stdout}"
    assert "favorites テーブルの移行を開始..." in result.stdout
    assert "vocab_status テーブルの移行を開始..." in result.stdout
    assert "データ移行プロセスが完了しました。" in result.stdout

    # ユーザーが作成されたことを確認
    cursor.execute("SELECT id FROM users WHERE username = 'default_user'")
    user_id = cursor.fetchone()["id"]
    assert user_id is not None

    # favoritesが移行されたことを確認
    cursor.execute("SELECT word_uuid FROM user_favorites WHERE user_id = ?", (user_id,))
    fav_entries = cursor.fetchall()
    assert len(fav_entries) == 1
    assert fav_entries[0]["word_uuid"] == fav_uuid

    # vocab_statusが移行されたことを確認
    cursor.execute(
        "SELECT word_uuid, status FROM user_vocab_status WHERE user_id = ?", (user_id,)
    )
    status_entries = cursor.fetchall()
    assert len(status_entries) == 1
    assert status_entries[0]["word_uuid"] == status_uuid
    assert status_entries[0]["status"] == "active"


def test_migrate_user_data_old_db_not_found():
    """
    migrate-user-dataコマンドが、古いDBファイルが見つからない場合にエラーを出すことを確認
    """
    result = runner.invoke(
        app, ["migrate-user-data", "--old-db-path", "nonexistent.db"]
    )
    assert result.exit_code == 1
    assert (
        "エラー: 移行元データベース 'nonexistent.db' が見つかりません。"
        in result.output
    )

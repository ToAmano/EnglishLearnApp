import csv
import sqlite3
import uuid
from pathlib import Path

import typer

from ..db_manager import WORD_DATA_DIR, get_db_connection, init_db


def consolidate_words(
    data_dir: Path = typer.Option(
        WORD_DATA_DIR,
        "--data-dir",
        "-d",
        help="単語データCSVファイルが格納されているディレクトリのパス。",
    )
):
    """
    consolidate-words

    説明
    指定されたディレクトリにあるCSVファイルから単語データを統合し、重複を排除してデータベースに登録します。
    新しい単語は追加され、既存の単語の `is_active` ステータスは更新されます。CSVに存在しなくなった単語は非アクティブ化されます。

    使用方法
    ```bash
    python -m src.data_pipeline.main consolidate-words [OPTIONS]
    ```

    オプション
    *   `--data-dir`, `-d` (Path):
        *   説明: 単語データCSVファイルが格納されているディレクトリのパス。
        *   デフォルト: `src/data/word_data`

    例
    ```bash
    # デフォルトのデータディレクトリを使用して単語を統合する
    python -m src.data_pipeline.main consolidate-words

    # 特定のディレクトリにあるCSVファイルから単語を統合する
    python -m src.data_pipeline.main consolidate-words --data-dir /path/to/my/csv_files
    englishapp consolidate-words --data-dir ./src/data/word_data/
    ```
    """
    typer.echo("単語データの統合を開始します...")

    if not data_dir.exists():
        typer.echo(
            f"エラー: 単語データディレクトリ '{data_dir}' が見つかりません。", err=True
        )
        raise typer.Exit(code=1)

    conn = get_db_connection()
    with conn:
        # 外部キー制約を有効にする (SQLiteのデフォルトは無効)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        init_db(conn)  # テーブルが存在しない場合は作成

        # 現在DBに存在する単語をキャッシュ (word_text -> {id, uuid, is_active, original_word_id})
        db_words_map = {
            row["word"]: {
                "id": row["id"],
                "uuid": row["uuid"],
                "is_active": bool(row["is_active"]),
                "original_word_id": row["original_word_id"],
            }
            for row in cursor.execute(
                "SELECT id, uuid, word, is_active, original_word_id FROM words"
            ).fetchall()
        }

        # 現在DBに存在するソースをキャッシュ (name -> id)
        existing_sources = {
            row["name"]: row["id"]
            for row in cursor.execute("SELECT id, name FROM sources").fetchall()
        }

        # CSVから読み込んだ単語のセット (word_text)
        words_from_csv = set()

        # word_source_links と word_meanings を一度クリアし、現在のCSVに基づいて再構築する
        cursor.execute("DELETE FROM word_source_links")
        cursor.execute(
            "DELETE FROM word_meanings"
        )  # 意味はCSVから直接読み込まないため、ここでクリア

        for csv_file in data_dir.glob("*.csv"):
            typer.echo(f"処理中: {csv_file.name}")

            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word_text = row.get("word")
                    source_name_from_csv = row.get(
                        "source"
                    )  # CSVからsourceカラムを読み込む
                    original_word_id = int(row.get("word_id", 0))

                    if not word_text:
                        typer.echo(
                            f"警告: {csv_file.name} の行に 'word' カラムがありません。スキップします。",
                            err=True,
                        )
                        continue

                    if not source_name_from_csv:
                        typer.echo(
                            f"警告: {csv_file.name} の単語 '{word_text}' に 'source' カラムがありません。スキップします。",
                            err=True,
                        )
                        continue

                    # ソースを登録または取得
                    if source_name_from_csv not in existing_sources:
                        cursor.execute(
                            "INSERT INTO sources (name) VALUES (?)",
                            (source_name_from_csv,),
                        )
                        source_id = cursor.lastrowid
                        existing_sources[source_name_from_csv] = source_id
                    else:
                        source_id = existing_sources[source_name_from_csv]

                    # 単語をDBに登録または更新
                    if word_text not in db_words_map:
                        # 新規単語: UUIDを生成して挿入
                        new_uuid = str(uuid.uuid4())
                        cursor.execute(
                            "INSERT INTO words (uuid, word, original_word_id, is_active) VALUES (?, ?, ?, ?)",
                            (new_uuid, word_text, original_word_id, True),
                        )
                        db_words_map[word_text] = {
                            "id": cursor.lastrowid,
                            "uuid": new_uuid,
                            "is_active": True,
                            "original_word_id": original_word_id,
                        }
                        # CSVにmeaningカラムがないため、word_meaningsへの挿入は行わない
                        # 意味は別途生成または追加されることを想定
                    elif not db_words_map[word_text]["is_active"]:
                        # 既存単語だが非アクティブだった場合、アクティブに戻す
                        cursor.execute(
                            "UPDATE words SET is_active = ? WHERE uuid = ?",
                            (True, db_words_map[word_text]["uuid"]),
                        )
                        db_words_map[word_text]["is_active"] = True

                    # original_word_idがより小さい場合のみ更新
                    current_original_id = db_words_map[word_text]["original_word_id"]
                    if original_word_id > 0 and (
                        current_original_id is None
                        or original_word_id < current_original_id
                    ):
                        cursor.execute(
                            "UPDATE words SET original_word_id = ? WHERE uuid = ?",
                            (original_word_id, db_words_map[word_text]["uuid"]),
                        )
                        db_words_map[word_text]["original_word_id"] = original_word_id

                    words_from_csv.add(word_text)

                    # word_source_links を再構築するために、現在の単語のuuidを取得
                    current_word_uuid = db_words_map[word_text]["uuid"]

                    # 単語とソースのリンクを登録 (重複は無視)
                    try:
                        cursor.execute(
                            "INSERT INTO word_source_links (word_uuid, source_id) VALUES (?, ?)",
                            (current_word_uuid, source_id),
                        )
                    except sqlite3.IntegrityError:
                        # 既にリンクが存在する場合は何もしない (PRIMARY KEY制約による)
                        pass

        # CSVに存在しない単語を非アクティブ化 (ソフトデリート)
        for word_text, details in db_words_map.items():
            if word_text not in words_from_csv and details["is_active"]:
                typer.echo(
                    f"単語 '{word_text}' がCSVから削除されたため、非アクティブ化します。"
                )
                cursor.execute(
                    "UPDATE words SET is_active = ? WHERE uuid = ?",
                    (False, details["uuid"]),
                )
                details["is_active"] = False  # キャッシュも更新

        conn.commit()
    typer.echo("単語データの統合が完了しました。")

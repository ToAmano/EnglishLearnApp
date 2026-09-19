"""
新しい設計のDBに古いDBからデータを移行するコマンド。
特に
- お気に入り単語
- 学習ステータス
を移行する。

"""

from pathlib import Path

import typer

from ..db_manager import get_db_connection


def migrate_user_data(
    old_db_path: Path = typer.Option(
        ..., "--old-db-path", help="移行元の古いuser.dbファイルのパス。"
    ),
):
    """
    migrate-user-data

    説明
    古いuser.dbから新しい統合データベースへユーザーデータを移行します。
    このコマンドは、古いユーザーのお気に入りや学習ステータスを新しいデータベース構造にマッピングします。

    使用方法
    ```bash
    python -m src.data_pipeline.main migrate-user-data [OPTIONS]
    ```

    オプション
    *   `--old-db-path` (Path):
        *   説明: 移行元の古いuser.dbファイルのパス。
        *   必須: はい

    例
    ```bash
    # /path/to/old/user.db からユーザーデータを移行する
    python -m src.data_pipeline.main migrate-user-data --old-db-path /path/to/old/user.db
    ```
    """
    typer.echo(f"古いデータベース '{old_db_path}' からのデータ移行を開始します...")

    if not old_db_path.exists():
        typer.echo(
            f"エラー: 移行元データベース '{old_db_path}' が見つかりません。", err=True
        )
        raise typer.Exit(code=1)

    new_conn = get_db_connection()
    old_conn = get_db_connection(db_path=old_db_path)

    try:
        new_cursor = new_conn.cursor()
        old_cursor = old_conn.cursor()

        # 1. デフォルトユーザーの作成/取得
        default_username = "default_user"
        new_cursor.execute(
            "SELECT id FROM users WHERE username = ?", (default_username,)
        )
        user_row = new_cursor.fetchone()
        if user_row:
            target_user_id = user_row["id"]
            typer.echo(
                f"既存のユーザー '{default_username}' (ID: {target_user_id}) を使用します。"
            )
        else:
            # 簡単なハッシュ化（本番ではbcryptなどを使用）
            hashed_password = "default_password_hashed"
            new_cursor.execute(
                "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                (default_username, hashed_password),
            )
            target_user_id = new_cursor.lastrowid
            typer.echo(
                f"新しいデフォルトユーザー '{default_username}' (ID: {target_user_id}) を作成しました。"
            )

        # 2. 単語テキスト -> UUID の対応表を作成
        new_cursor.execute("SELECT word, uuid FROM words")
        word_to_uuid_map = {row["word"]: row["uuid"] for row in new_cursor.fetchall()}
        typer.echo(f"{len(word_to_uuid_map)}件の単語マッピングを作成しました。")

        # 3. favorites テーブルの移行
        typer.echo("favorites テーブルの移行を開始...")
        old_cursor.execute("SELECT word FROM favorites")
        old_favorites = old_cursor.fetchall()
        new_favorites = []
        migrated_count = 0
        skipped_count = 0
        for row in old_favorites:
            word_text = row["word"]
            word_uuid = word_to_uuid_map.get(word_text)
            if word_uuid:
                new_favorites.append((target_user_id, word_uuid))
                migrated_count += 1
            else:
                typer.echo(
                    f"警告: favoritesの単語 '{word_text}' は新しいDBに存在しないため、スキップします。",
                    err=True,
                )
                skipped_count += 1

        if new_favorites:
            new_cursor.executemany(
                "INSERT OR IGNORE INTO user_favorites (user_id, word_uuid) VALUES (?, ?)",
                new_favorites,
            )
        typer.echo(
            f"favorites の移行完了: {migrated_count}件を移行, {skipped_count}件をスキップ。"
        )

        # 4. vocab_status テーブルの移行
        typer.echo("vocab_status テーブルの移行を開始...")
        old_cursor.execute("SELECT word, status FROM vocab_status")
        old_statuses = old_cursor.fetchall()
        new_statuses = []
        migrated_count = 0
        skipped_count = 0
        for row in old_statuses:
            word_text, status = row["word"], row["status"]
            word_uuid = word_to_uuid_map.get(word_text)
            if word_uuid:
                new_statuses.append((target_user_id, word_uuid, status))
                migrated_count += 1
            else:
                typer.echo(
                    f"警告: vocab_statusの単語 '{word_text}' は新しいDBに存在しないため、スキップします。",
                    err=True,
                )
                skipped_count += 1

        if new_statuses:
            new_cursor.executemany(
                "INSERT OR IGNORE INTO user_vocab_status (user_id, word_uuid, status) VALUES (?, ?, ?)",
                new_statuses,
            )
        typer.echo(
            f"vocab_status の移行完了: {migrated_count}件を移行, {skipped_count}件をスキップ。"
        )

        new_conn.commit()
        typer.echo("データベースの変更をコミットしました。")

    finally:
        new_conn.close()
        old_conn.close()
        typer.echo("データベース接続を閉じました。")

    typer.echo("データ移行プロセスが完了しました。")

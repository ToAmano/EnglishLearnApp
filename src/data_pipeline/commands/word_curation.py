import sqlite3

import typer

from ..db_manager import get_db_connection

curate_app = typer.Typer()


@curate_app.command()
def rename(
    from_word: str = typer.Option(..., "--from", help="修正元の古い単語。"),
    to_word: str = typer.Option(..., "--to", help="修正先の新しい単語。"),
):
    """
    curate-words rename

    説明
    単語のスペルミスを修正します（リネーム）。データベース内の単語を新しいスペルに更新し、
    関連するすべてのデータ（説明文、お気に入り、学習ステータスなど）が新しい単語に引き継がれます。
    この操作は、ソースCSVファイルの手動修正が必要になることに注意してください。

    使用方法
    ```bash
    python -m src.data_pipeline.main curate-words rename [OPTIONS]
    ```

    オプション
    *   `--from` (String):
        *   説明: 修正元の古い単語。
        *   必須: はい
    *   `--to` (String):
        *   説明: 修正先の新しい単語。
        *   必須: はい

    例
    ```bash
    # データベース内の「aple」という単語を「apple」にリネームする
    python -m src.data_pipeline.main curate-words rename --from aple --to apple
    ```
    """
    typer.echo(f"単語のリネームを開始: '{from_word}' -> '{to_word}'")

    conn = get_db_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1. 修正元と修正先の単語の存在をチェック
        from_word_row = cursor.execute(
            "SELECT uuid FROM words WHERE word = ?", (from_word,)
        ).fetchone()
        to_word_row = cursor.execute(
            "SELECT uuid FROM words WHERE word = ?", (to_word,)
        ).fetchone()

        if not from_word_row:
            typer.secho(
                f"エラー: 修正元の単語 '{from_word}' がデータベースに存在しません。",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        if to_word_row:
            typer.secho(
                f"エラー: 修正先の単語 '{to_word}' は既にデータベースに存在します。",
                fg=typer.colors.RED,
            )
            typer.echo(
                "もし意図しない重複であれば、先にその単語を削除または別の単語にリネームしてください。"
            )
            raise typer.Exit(code=1)

        # 2. 単語テキストを更新
        try:
            cursor.execute(
                "UPDATE words SET word = ? WHERE word = ?", (to_word, from_word)
            )
            conn.commit()
            typer.secho(
                f"成功: 単語 '{from_word}' を '{to_word}' にリネームしました。",
                fg=typer.colors.GREEN,
            )
            typer.echo(
                "UUIDとすべての関連データ（説明文、お気に入り等）は引き継がれました。"
            )
            typer.echo(
                "注意: 次に `consolidate-words` を実行する前に、CSVソースファイルも手動で修正してください。"
            )
        except sqlite3.IntegrityError as e:
            conn.rollback()
            typer.secho(
                f"エラー: データベースの更新に失敗しました。'{to_word}' は既に存在する可能性があります。詳細: {e}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

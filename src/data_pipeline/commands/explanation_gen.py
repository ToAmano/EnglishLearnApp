import asyncio

import typer
from tqdm import tqdm

from ..db_manager import get_db_connection
from ..steps.generate_explanations import generate_explanation_for_word

app = typer.Typer()


async def worker(word_id, word_text, semaphore, pbar):
    """非同期で単語の説明文を生成するワーカー"""
    async with semaphore:
        try:
            explanation = await generate_explanation_for_word(word_text)
            pbar.update(1)
            return word_id, explanation
        except Exception as e:
            typer.echo(
                f"\nエラー: 単語 '{word_text}' (ID: {word_id}) の説明文生成に失敗 - {e}",
                err=True,
            )
            pbar.update(1)
            return word_id, None


async def _async_generate_explanations(limit: int, concurrency: int):
    """非同期で説明文を生成し、DBに保存するコアロジック"""
    typer.echo("説明文の生成を開始します...")

    conn = get_db_connection()
    try:
        # 1. 対象単語の選定
        query = (
            "SELECT id, word FROM words WHERE explanation IS NULL OR explanation = ''"
        )
        if limit > 0:
            query += f" LIMIT {limit}"

        target_words = conn.execute(query).fetchall()

        if not target_words:
            typer.echo("説明文が未生成の単語はありませんでした。")
            return

        typer.echo(
            f"{len(target_words)}件の単語の説明文を生成します（同時実行数: {concurrency}）。"
        )

        # 2. 非同期タスクの準備と実行
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)

        with tqdm(total=len(target_words)) as pbar:
            for row in target_words:
                task = worker(row["id"], row["word"], semaphore, pbar)
                tasks.append(task)

            results = await asyncio.gather(*tasks)

        # 3. データベースの更新
        successful_updates = 0
        updates = []
        for word_id, explanation in results:
            if explanation is not None:
                updates.append((explanation, word_id))
                successful_updates += 1

        if updates:
            typer.echo(
                f"\n{successful_updates}件の新しい説明文をデータベースに保存しています..."
            )
            cursor = conn.cursor()
            cursor.executemany("UPDATE words SET explanation = ? WHERE id = ?", updates)
            conn.commit()
            typer.echo("データベースの更新が完了しました。")
        else:
            typer.echo("\n更新する説明文はありませんでした。")

    finally:
        conn.close()

    typer.echo("説明文の生成プロセスが完了しました。")


def generate_explanations(
    limit: int = typer.Option(
        0, "--limit", "-l", help="処理する単語の最大数を指定します（0は無制限）"
    ),
    concurrency: int = typer.Option(
        5, "--concurrency", "-n", help="非同期実行の同時実行数"
    ),
):
    """
    generate-explanations

    説明
    データベース内の説明文が未生成の単語に対して、説明文を非同期で生成し、結果をデータベースに保存します。
    このコマンドは外部のAIサービスを利用します。

    使用方法
    ```bash
    python -m src.data_pipeline.main generate-explanations [OPTIONS]
    ```

    オプション
    *   `--limit`, `-l` (Integer):
        *   説明: 処理する単語の最大数を指定します（0は無制限）。
        *   デフォルト: `0`
    *   `--concurrency`, `-n` (Integer):
        *   説明: 非同期実行の同時実行数。
        *   デフォルト: `5`

    例
    ```bash
    # 説明文が未生成のすべての単語に対して説明文を生成する
    python -m src.data_pipeline.main generate-explanations

    # 説明文が未生成の単語のうち、最初の100件に対して説明文を生成する
    python -m src.data_pipeline.main generate-explanations --limit 100

    # 同時実行数を10に設定して説明文を生成する
    python -m src.data_pipeline.main generate-explanations --concurrency 10
    ```
    """
    asyncio.run(_async_generate_explanations(limit=limit, concurrency=concurrency))

import csv
from pathlib import Path

import typer
from spellchecker import SpellChecker

from ..db_manager import WORD_DATA_DIR


def check_spelling(
    data_dir: Path = typer.Option(
        WORD_DATA_DIR,
        "--data-dir",
        "-d",
        help="単語データCSVファイルが格納されているディレクトリのパス。",
    ),
    lang: str = typer.Option(
        "en", "--lang", "-l", help="スペルチェックに使用する言語 (例: en, es, fr)。"
    ),
):
    """
    check-spelling

    説明
    指定されたディレクトリのCSVファイル内の単語のスペルをファイルごとにチェックします。
    スペルミスの可能性のある単語と、その修正候補を提示します。

    使用方法
    ```bash
    python -m src.data_pipeline.main check-spelling [OPTIONS]
    englishapp check-spelling --data-dir ./src/data/word_data/
    ```

    オプション
    *   `--data-dir`, `-d` (Path):
        *   説明: 単語データCSVファイルが格納されているディレクトリのパス。
        *   デフォルト: `src/data/word_data`
    *   `--lang`, `-l` (String):
        *   説明: スペルチェックに使用する言語 (例: en, es, fr)。
        *   デフォルト: `"en"`

    例
    ```bash
    # デフォルトのデータディレクトリにある単語のスペルをチェックする
    python -m src.data_pipeline.main check-spelling

    # 特定のディレクトリにある単語のスペルをチェックする
    python -m src.data_pipeline.main check-spelling --data-dir /path/to/my/csv_files

    # スペルチェックの言語をスペイン語に設定する
    python -m src.data_pipeline.main check-spelling --lang es
    ```
    """
    typer.echo(f"ディレクトリ '{data_dir}' のスペルチェックを開始します...")

    if not data_dir.exists():
        typer.echo(
            f"エラー: データディレクトリ '{data_dir}' が見つかりません。", err=True
        )
        raise typer.Exit(code=1)

    try:
        spell = SpellChecker(language=lang)
    except ValueError as e:
        typer.echo(f"エラー: 言語 '{lang}' の辞書が見つかりません。{e}", err=True)
        raise typer.Exit(code=1)

    total_misspelled_count = 0

    all_csv_files = sorted(list(data_dir.glob("*.csv")))

    for csv_file in all_csv_files:
        words_in_file = set()
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word_text = row.get("word")
                if word_text:
                    # ハイフンやスペースを含む単語は個別の単語に分割してチェック
                    for sub_word in word_text.replace("-", " ").split():
                        sub_word = sub_word.strip().lower()
                        if sub_word:
                            words_in_file.add(sub_word)

        if not words_in_file:
            continue

        misspelled_words = spell.unknown(words_in_file)

        if misspelled_words:
            total_misspelled_count += len(misspelled_words)
            typer.echo("\n---")
            typer.secho(f"ファイル: {csv_file.name}", fg=typer.colors.YELLOW)
            typer.echo("---")
            for i, word in enumerate(sorted(list(misspelled_words)), 1):
                candidates = spell.candidates(word)
                typer.echo(f"{i}. 単語: ", nl=False)
                typer.secho(f"'{word}'", fg=typer.colors.RED)
                if candidates:
                    typer.echo(f"   修正候補: {', '.join(candidates)}")
                else:
                    typer.echo("   修正候補は見つかりませんでした。")

    if total_misspelled_count == 0:
        typer.secho(
            "\nスペルミスの可能性がある単語は見つかりませんでした。",
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho(
            f"\n合計 {total_misspelled_count} 件のスペルミスの可能性がある単語が見つかりました。",
            bold=True,
        )

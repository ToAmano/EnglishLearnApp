import argparse
import csv
import shutil
from pathlib import Path


def modify_word_ids(file_path: Path, offset: int) -> None:
    """
    指定されたCSVファイルのword_idカラムにオフセット値を加算します。

    Args:
        file_path: 修正するCSVファイルへのパス。
        offset: word_idに加算する整数値。
    """
    if not file_path.is_file():
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return

    print(f"ファイル '{file_path}' のword_idを修正中 (オフセット: {offset})...")

    rows = []
    fieldnames = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            if "word_id" not in fieldnames:
                print(
                    f"エラー: '{file_path}' に 'word_id' カラムが見つかりません。 {fieldnames}"
                )
                return

            for row in reader:
                try:
                    original_id = int(row["word_id"])
                    row["word_id"] = str(original_id + offset)
                except (ValueError, TypeError):
                    print(
                        f"警告: '{file_path}' のword_idが不正な行をスキップします: {row.get('word_id')}"
                    )
                rows.append(row)
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 元のファイルをバックアップし、新しいデータで上書きする
    backup_path = file_path.with_suffix(".csv.bak")
    try:
        shutil.copy(file_path, backup_path)
        with open(file_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(
            f"'{file_path}' のword_idを正常に修正しました。元のファイルは '{backup_path}' にバックアップされています。"
        )
    except Exception as e:
        print(f"ファイルの書き込み中にエラーが発生しました: {e}")
        # 失敗した場合はバックアップから復元を試みる
        if backup_path.is_file():
            shutil.copy(backup_path, file_path)
            print(f"エラー発生のため、'{file_path}' をバックアップから復元しました。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CSVファイルのword_idカラムにオフセット値を加算します。"
    )
    parser.add_argument(
        "--file", type=Path, required=True, help="修正するCSVファイルへのパス。"
    )
    parser.add_argument(
        "--offset", type=int, required=True, help="word_idに加算する整数値。"
    )
    args = parser.parse_args()

    modify_word_ids(args.file, args.offset)

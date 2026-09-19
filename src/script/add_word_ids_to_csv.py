import argparse
import csv
import shutil
from pathlib import Path


def add_word_ids_to_csv(file_path: Path, start_id: int) -> None:
    """
    指定されたCSVファイルにword_idカラムを追加し、連番を振ります。

    Args:
        file_path: 修正するCSVファイルへのパス。
        start_id: word_idの採番を開始する整数値。
    """
    if not file_path.is_file():
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return

    print(f"ファイル '{file_path}' にword_idカラムを追加中 (開始ID: {start_id})...")

    rows = []
    fieldnames = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            if "word_id" in fieldnames:
                print(
                    f"エラー: '{file_path}' に 'word_id' カラムが既に存在します。処理を中断します。"
                )
                return

            # 新しいfieldnamesを作成 (word_idを先頭に追加)
            new_fieldnames = ["word_id"] + [f for f in fieldnames if f != "word_id"]

            current_id = start_id
            for row in reader:
                new_row = {"word_id": str(current_id)}
                new_row.update(row)  # 既存のデータを追加
                rows.append(new_row)
                current_id += 1
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 元のファイルをバックアップし、新しいデータで上書きする
    backup_path = file_path.with_suffix(".csv.bak")
    try:
        shutil.copy(file_path, backup_path)
        with open(file_path, "w", encoding="utf-8-sig", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(
            f"'{file_path}' にword_idを正常に追加しました。元のファイルは '{backup_path}' にバックアップされています。"
        )
    except Exception as e:
        print(f"ファイルの書き込み中にエラーが発生しました: {e}")
        # 失敗した場合はバックアップから復元を試みる
        if backup_path.is_file():
            shutil.copy(backup_path, file_path)
            print(f"エラー発生のため、'{file_path}' をバックアップから復元しました。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CSVファイルにword_idカラムを追加し、連番を振ります。"
    )
    parser.add_argument(
        "--file", type=Path, required=True, help="修正するCSVファイルへのパス。"
    )
    parser.add_argument(
        "--start-id", type=int, required=True, help="word_idの採番を開始する整数値。"
    )
    args = parser.parse_args()

    add_word_ids_to_csv(args.file, args.start_id)

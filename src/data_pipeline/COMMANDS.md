# コマンドラインツール ドキュメンテーション

このドキュメントでは、`src/data_pipeline` にあるコマンドラインツールの各コマンドとその使用方法について説明します。

---

## 1. `consolidate-words`

### 説明
指定されたディレクトリにあるCSVファイルから単語データを統合し、重複を排除してデータベースに登録します。新しい単語は追加され、既存の単語の `is_active` ステータスは更新されます。CSVに存在しなくなった単語は非アクティブ化されます。

### 使用方法
```bash
python -m src.data_pipeline.main consolidate-words [OPTIONS]
```

### オプション
*   `--data-dir`, `-d` (Path):
    *   説明: 単語データCSVファイルが格納されているディレクトリのパス。
    *   デフォルト: `src/data/word_data`

### 例
```bash
# デフォルトのデータディレクトリを使用して単語を統合する
python -m src.data_pipeline.main consolidate-words

# 特定のディレクトリにあるCSVファイルから単語を統合する
python -m src.data_pipeline.main consolidate-words --data-dir /path/to/my/csv_files
```

---

## 2. `generate-explanations`

### 説明
データベース内の説明文が未生成の単語に対して、説明文を非同期で生成し、結果をデータベースに保存します。このコマンドは外部のAIサービスを利用します。

### 使用方法
```bash
python -m src.data_pipeline.main generate-explanations [OPTIONS]
```

### オプション
*   `--limit`, `-l` (Integer):
    *   説明: 処理する単語の最大数を指定します（0は無制限）。
    *   デフォルト: `0`
*   `--concurrency`, `-n` (Integer):
    *   説明: 非同期実行の同時実行数。
    *   デフォルト: `5`

### 例
```bash
# 説明文が未生成のすべての単語に対して説明文を生成する
python -m src.data_pipeline.main generate-explanations

# 説明文が未生成の単語のうち、最初の100件に対して説明文を生成する
python -m src.data_pipeline.main generate-explanations --limit 100

# 同時実行数を10に設定して説明文を生成する
python -m src.data_pipeline.main generate-explanations --concurrency 10
```

---

## 3. `migrate-user-data`

### 説明
古いuser.dbから新しい統合データベースへユーザーデータを移行します。このコマンドは、古いユーザーのお気に入りや学習ステータスを新しいデータベース構造にマッピングします。

### 使用方法
```bash
python -m src.data_pipeline.main migrate-user-data [OPTIONS]
```

### オプション
*   `--old-db-path` (Path):
    *   説明: 移行元の古いuser.dbファイルのパス。
    *   必須: はい

### 例
```bash
# /path/to/old/user.db からユーザーデータを移行する
python -m src.data_pipeline.main migrate-user-data --old-db-path /path/to/old/user.db
```

---

## 4. `check-spelling`

### 説明
指定されたディレクトリのCSVファイル内の単語のスペルをファイルごとにチェックします。スペルミスの可能性のある単語と、その修正候補を提示します。

### 使用方法
```bash
python -m src.data_pipeline.main check-spelling [OPTIONS]
```

### オプション
*   `--data-dir`, `-d` (Path):
    *   説明: 単語データCSVファイルが格納されているディレクトリのパス。
    *   デフォルト: `src/data/word_data`
*   `--lang`, `-l` (String):
    *   説明: スペルチェックに使用する言語 (例: en, es, fr)。
    *   デフォルト: `"en"`

### 例
```bash
# デフォルトのデータディレクトリにある単語のスペルをチェックする
python -m src.data_pipeline.main check-spelling

# 特定のディレクトリにある単語のスペルをチェックする
python -m src.data_pipeline.main check-spelling --data-dir /path/to/my/csv_files

# スペルチェックの言語をスペイン語に設定する
python -m src.data_pipeline.main check-spelling --lang es
```

---

## 5. `curate-words rename`

### 説明
単語のスペルミスを修正します（リネーム）。データベース内の単語を新しいスペルに更新し、関連するすべてのデータ（説明文、お気に入り、学習ステータスなど）が新しい単語に引き継がれます。この操作は、ソースCSVファイルの手動修正が必要になることに注意してください。

### 使用方法
```bash
python -m src.data_pipeline.main curate-words rename [OPTIONS]
```

### オプション
*   `--from` (String):
    *   説明: 修正元の古い単語。
    *   必須: はい
*   `--to` (String):
    *   説明: 修正先の新しい単語。
    *   必須: はい

### 例
```bash
# データベース内の「aple」という単語を「apple」にリネームする
python -m src.data_pipeline.main curate-words rename --from aple --to apple
```

# AGENTS.md

EnglishLearnApp で作業するコーディングエージェント向けのガイド。

## プロジェクト概要

英日辞書 + 語彙学習アプリ。4 つの部分から成る。

| 部分 | 場所 | 状態 |
|---|---|---|
| Streamlit フロントエンド | `src/app.py`, `src/frontend/` | 現行のメイン UI |
| FastAPI バックエンド | `src/api.py` | 最小限（`/api/favorites` のみ） |
| React フロントエンド | `src/frontend_react/` | 開発中（雛形段階） |
| データパイプライン CLI | `src/data_pipeline/` | Typer ベース、`englishapp` コマンド |

`TODO.md` にある通り、API を Flask で書き直す構想があるが未着手（現状は FastAPI）。

## 最重要: 実行時の前提

この 2 点を外すとほぼ何も動かない。

### 1. カレントディレクトリは `src/`

DB パスのデフォルトは `db_core.py` で `"database/words.db"` / `"database/user.db"` という **cwd 相対**のパス。実体は `src/database/` にあるので、**`src/` から起動しないと `sqlite3.OperationalError: unable to open database file` になる**（リポジトリルートに `database/` は存在しない）。

```bash
cd src
streamlit run app.py          # Streamlit UI
uvicorn api:app --reload      # FastAPI
```

環境変数 `WORDS_DB_PATH` / `USER_DB_PATH` で上書きすれば任意の cwd から動かせる。

> 注: `.env` には `WORD_DB_PATH`（S 抜け）と書かれているが、コードが読むのは `WORDS_DB_PATH`。この .env の行は**効いていない**。修正する場合は両方の整合を確認すること。

### 2. Python は 3.10 以上が必須

`db_core.py` などが `Any | None` 形式の型注釈を使うため 3.10+ が要る。ただし `pyproject.toml` の `requires-python` は `>=3.9` のまま（実態と不一致）。

この環境では PATH 先頭の `python` / `python3` が anaconda の **3.9.18** で、import した時点で `TypeError: unsupported operand type(s) for |` になる。動作確認済みの interpreter は `/opt/homebrew/bin/python3.13`。

```bash
cd src && /opt/homebrew/bin/python3.13 -c "import sys; sys.path.insert(0,'.'); ..."
```

CI は pre-commit が 3.11、Azure デプロイが 3.12 を使う。

## データベース構成

**2 つの独立した SQLite DB** があり、さらにデータパイプラインは**3 つ目の別スキーマの DB** を使う。混同しないこと。

### `src/database/words.db` — 辞書 DB（`get_db_connection()`）

主キーは `word_id` (INTEGER)。

- `words` (word_id, word, source)
- `meanings` (word_id, meaning, part_of_speech, category)
- `examples` (word_id, example, audio_path)
- `word_explanations` (word_id, explanation) — AI 生成の日本語解説
- `stems` / `derived_words` — 語幹と派生語の多対多
- `synonyms` (word_id_1, word_id_2) — 双方向エッジ
- `search_logs` (word_id, count)
- `vocab_status` (word_id, status) — **非推奨。user.db 側を使う**
- `favorites` (word_id) — **非推奨。user.db 側を使う**

### `src/database/user.db` — ユーザ DB（`get_user_db_connection()`）

主キーは `word` (TEXT)。

- `favorites` (word)
- `vocab_status` (word, status CHECK in 'unknown'/'passive'/'active')

**辞書 DB は `word_id`、ユーザ DB は `word` が主キー**という非対称がこのコードベース最大の落とし穴。変換は `src/backend/core/db_core.py` の `get_wordid_from_word()` / `get_word_from_wordid()` が担う。`get_wordid_from_word()` は**未登録語に対して例外ではなく `0` を返す**ので、呼び出し側でのチェックが必要。

### `instance/words.db` — データパイプライン専用 DB

`src/data_pipeline/db_manager.py` が扱う、上記とは**完全に別スキーマ**の DB（`users` テーブル、`uuid` 列、`id` 主キーなど）。`DATABASE_PATH` 環境変数で上書き可（デフォルト `instance/words.db`、cwd 相対なのでリポジトリルートから実行する前提）。`englishapp` CLI の変更がアプリ本体の辞書 DB に反映されるわけではない点に注意。

### DB の初期化

`src/database/step01_*.py` は `sqlite3.connect("words.db")` のように**ファイル名直書き**なので、`src/database/` 内で実行する前提。

```bash
cd src/database
python3.13 step01_init_database_dictionary.py
python3.13 step01_init_database_user.py
python3.13 step02_add_database_dictionary.py
```

`.db` ファイルは gitignore されておらず**リポジトリにコミットされている**。DB を触る変更は差分に出るので、意図しない DB の更新を混ぜないこと。

## コード構成

### `src/backend/` — ビジネスロジック

DB アクセスを抽象化する層。Streamlit / FastAPI の両方から呼ばれる。

- `backend.py` — `search_meanings`, `get_examples`, `get_derived_words`, `find_synonym_ids`, `fetch_word_info`, `get_synonyms`
- `favorite.py` — `is_favorited`, `toggle_favorite`, `get_favorites_words`
- `vocab_status.py` — `get_vocab_status`, `set_vocab_status`
- `search_count.py` — `get_search_count`, `increment_search_count`
- `explanation.py` — `get_explanation`
- `learning.py` — `get_word_batch`（学習用の単語選択）
- `core/db_core.py` — 接続と word/word_id 変換

import は `from backend.core.db_core import ...` のように **`src/` を起点とした絶対 import**。`src` パッケージ経由（`from src.backend...`）ではない点に注意（テストだけが `src.` 形式を使っており不整合）。

`find_synonym_ids()` は `synonyms` の双方向エッジを**幅優先探索**し、直接の隣接だけでなく連結成分全体を返す。

### `src/frontend/` — Streamlit UI

タブごとにモジュールを分割。各モジュールは `render()` を公開し、`app.py` が呼ぶ。

- `tab1_search.py` — 単語検索
- `tab4_favorite.py` — お気に入り
- `tab5_wordbatch.py` — バッチ確認モード
- `tab6_wordcard.py` — 単語カードモード
- `core.py` — 共通部品（`show_status`, `show_favorite`, `render_speak_button`, `render_explanation`）

タブ 2（単語テスト）とタブ 3（例文リスニング）は `app.py` 内にプレースホルダとして直書きされており未実装。

`st.session_state` のキー衝突が過去にバグ源になっている（コミット履歴参照）。共通部品に state を持たせる際は呼び出し元ごとに prefix を付けること。

### `src/data_pipeline/` — CLI

```bash
englishapp consolidate-words      # 単語リストの統合・重複排除
englishapp generate-explanations  # AI 解説生成 (LangChain + Google Generative AI)
englishapp migrate-user-data      # 旧スキーマからのユーザデータ移行
englishapp check-spelling         # スペルチェック
englishapp curate-words <sub>     # 単語キュレーション（サブコマンドあり）
englishapp generate-synonyms <sub># 類義語生成（サブコマンドあり）
```

エントリポイントは `src/data_pipeline/main.py`（`pyproject.toml` の `[project.scripts]` で登録）。新コマンドは `commands/` に追加して `main.py` で `app.command()` / `app.add_typer()` 登録する。

### `src/data/` — データファイル

- `word_data/` — レベル別・出典別の単語 CSV（eiken, lv1-lv12, buntan, supervocab 等）
- `explanation_data/` — 生成済み日本語解説 CSV
- `generate_examples/` — 例文生成の成果物と notebook
- `generate_synonym/` — 類義語生成の成果物と notebook
- `generate_audio/` — 音声生成の実験（notebook + wav）
- `generate_graphics/` — 画像生成の実験

notebook（`.ipynb`）は実験用で、確定したロジックは `data_pipeline/commands/` に移す方針。

### `src/script/` — 単発スクリプト

`add_word_ids_to_csv.py`, `modify_word_ids.py`, `pdf2wordlist.py`。パイプラインには組み込まれていない。

## コード品質

pre-commit が**かなり厳しい**設定。コミット前に必ず通すこと。

```bash
pre-commit install
pre-commit run --all-files
```

- **isort**（black profile）, **black**（line length 150）
- **mypy** `--strict --ignore-missing-imports` — **新規コードには完全な型注釈が必須**
- **flake8** — max-line-length 150, `--max-complexity 10`, `--max-expression-complexity 7`, `--max-cognitive-complexity 7`。無視: E402, E800, W503
  - 認知的複雑度 7 は厳しい。ネストした分岐は早期 return や関数抽出で割ること。
- **pylint** — line length 150, C0114/C0115/C0116（docstring 必須）は無効化済み。`init-hook` で `sys.path.insert(0, 'src')`、`pymupdf` は ignored-modules
- **flake8-eradicate**（E800 は無視設定だが）— コメントアウトされたコードは残さない方針。直近のコミットにも削除作業が複数ある
- `check-added-large-files --maxkb=50000` — CSV が大きいため上限が緩めてある

pylint の `additional_dependencies` には pandas, streamlit, langchain, dotenv, langchain_google_genai が列挙されている。**新しい依存を追加したら `.pre-commit-config.yaml` のこのリストも更新**しないと pylint が import エラーを出す。

## テスト

`tests/data_pipeline/test_commands.py` が 1 ファイルあるだけ。

**現状このテストは壊れている**: `pytest`, `typer.testing.CliRunner`, `pathlib.Path` を使っているのに import 文が無く、collection 時点で `NameError` になる。テストを触る場合はまず import を補うこと。

CI ではテストは実行されていない（Azure ワークフローに「Optional: Add step to run tests here」というコメントが残っているだけ）。

## CI / デプロイ

- `.github/workflows/pre-commit.yml` — `main` / `develop` への PR で pre-commit を全ファイル実行（Python 3.11）
- `.github/workflows/main_englishvocabulary.yml` — `main` への push で Azure Web App `EnglishVocabulary` にデプロイ（Python 3.12、`requirements.txt` を使用）

依存が `pyproject.toml` と `requirements.txt` の**2 箇所**にあり内容がずれている（`requirements.txt` にのみ pymupdf, typer, tqdm, pyspellchecker, pytest がある／`pyproject.toml` にのみ fastapi, uvicorn, python-multipart がある）。デプロイは `requirements.txt` を見るので、実行時に必要な依存はそちらにも入れること。

## 規約

- **コミットメッセージは日本語**。`✨`（機能追加）、`🐛 [bug fix]`（修正）といった絵文字プレフィックスが使われることがある
- ブランチは `feature/<name>` 形式。PR は `main` 宛て
- コード内のコメント・docstring は日本語と英語が混在。**周囲のファイルのスタイルに合わせる**
- 認証機能は未実装。`app.py` で `USER_ID = "default_user"` を使用
- 設定は `.env`（`python-dotenv` で読み込み）。`.env` は gitignore 対象

## 作業時の注意

1. **cwd と Python バージョン**を先に確認する（上記「最重要」節）
2. **DB ファイルの差分**を意図せず混ぜない。アプリを起動しただけで `search_logs` などが更新され `words.db` に差分が出る
3. **word / word_id の変換**を挟み忘れない。ユーザ DB に word_id を、辞書 DB に word を渡すバグが起きやすい
4. **`instance/words.db` と `src/database/words.db` は別物**。データパイプラインの話をしているのかアプリの話をしているのか常に区別する
5. **pre-commit を通してからコミット**する。特に mypy strict と cognitive-complexity 7 で弾かれやすい

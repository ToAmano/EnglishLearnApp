# Google OIDC認証 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the user selects delegation. Steps use checkbox syntax for tracking.

**Goal:** StreamlitでGoogleログインを必須にし、旧データを保持してユーザー別の学習データを保存する。

**Architecture:** OIDCの制御は `auth/oidc.py` に集約し、ユーザー識別と保存はStreamlitに依存しないバックエンドに分ける。認証済みGoogle subjectを内部UUIDに対応付け、各タブからバックエンドまでユーザーIDを明示的に渡す。

**Tech Stack:** Python 3.10以上、Streamlit標準OIDC、Authlib、SQLite、pytest、Streamlit AppTest。

**Spec:** `docs/superpowers/specs/2026-10-03-google-oidc-design.md`

## Global Constraints

- アプリは `src/` から起動する。テストは `PYTHONPATH=src` と一時DBを使用する。
- 認証は `st.login("google")`、`st.logout()`、`st.user`。独自トークン検証やトークン保存を追加しない。
- 設定は `[auth]` と `[auth.google]`、スコープは `openid profile email`。
- 旧テーブル、`default_user` の履歴・評価、辞書DB、パイプラインDBを保持する。
- 新規アカウントは空の学習データから開始する。引き継ぎコマンドと本番デプロイは対象外。
- 新規コードには完全な型注釈を付け、複雑度の上限は既存pre-commit設定に従う。
- 検索回数は従来の全体集計を維持する。

## Review Focus

- 同時に同一Google subjectで初回ログインしても内部UUIDが一つになることをTask 1で検証する。
- 不正・欠落した認証クレームでも旧ユーザーにフォールバックしないことをTask 3で検証する。
- アカウント変更後に入力途中の回答や選択状態が残らないことをTask 3で検証する。
- 同じ単語を検索タブとカードタブに表示してもキーが衝突しないことをTask 4で検証する。
- APIへ任意のユーザーIDを渡しても学習データを取得できないことをTask 5で検証する。

---

### Task 1: ユーザー識別と追加スキーマ

**Files:** Create `src/backend/users.py`, `src/backend/core/user_schema.py`, `tests/backend/test_users.py`; modify `src/backend/core/db_core.py`.

**Interfaces:** `initialize_user_schema() -> None`; `get_or_create_google_user(subject: str) -> str`。後者は追加スキーマを初期化し、Google subjectから内部UUIDを返す。ユーザDB接続で外部キー制約を有効化する。

- [ ] 一時DBのテストを書く。`test_same_subject_returns_same_user_id` は再実行でUUIDが等しく、別subjectでは異なることを検証する。
- [ ] `test_concurrent_creation_is_unique` は独立接続による並行登録で全戻り値とDBの行数が一つになることを検証する。
- [ ] `test_initialize_preserves_legacy_data` は旧favorites、vocab_status、練習履歴・評価の内容が初期化前後で等しいことを検証する。
- [ ] `test_invalid_subject_rejected` は空文字・空白を拒否し、ユーザーが追加されないことを検証する。
- [ ] `PYTHONPATH=src python3 -m pytest tests/backend/test_users.py -q` を実行して新機能未実装による失敗を確認する。
- [ ] users、user_favorites、user_vocab_statusを設計書どおり作成する。登録は一意制約とON CONFLICTで保護し、そのsubjectの既存IDを読み出す。
- [ ] 同じテストを再実行し、全件成功を確認する。

### Task 2: お気に入りと習得状態のユーザー分離

**Files:** Modify `src/backend/favorite.py`, `src/backend/vocab_status.py`; create `tests/backend/test_user_vocabulary.py`.

**Interfaces:** `is_favorited(word: str, user_id: str) -> bool`; `toggle_favorite(word: str, user_id: str) -> None`; `get_favorites_words(user_id: str) -> list[str]`; `get_vocab_status(word: str, user_id: str) -> str`; `set_vocab_status(word: str, status: str, user_id: str) -> None`。ユーザーIDにデフォルト値を設定しない。

- [ ] 二人の登録済みユーザーを使うテストを書く。片方の同じ単語への追加・解除・状態変更が他方に影響せず、旧テーブルの単語が一覧に出ないことを検証する。
- [ ] unknownの初期値、不正statusのValueError、存在しないユーザーへの書き込みの外部キーエラーを検証する。
- [ ] `PYTHONPATH=src python3 -m pytest tests/backend/test_user_vocabulary.py -q` で失敗を確認する。
- [ ] 全SQLを新しいユーザー別テーブルへ変更し、必ずuser_idとwordで対象を指定する。接続はclosingとトランザクションで管理する。
- [ ] Task 1とTask 2のテストを実行して成功を確認する。

### Task 3: 独立したOIDCログインモジュール

**Files:** Create `src/auth/__init__.py`, `src/auth/oidc.py`, `tests/auth/test_oidc.py`, `src/.streamlit/secrets.toml.example`; modify `.gitignore`, `pyproject.toml`, `requirements.txt`, `.pre-commit-config.yaml`.

**Interfaces:** `require_google_login() -> str` は認証済みの内部ユーザーIDを返す。未認証・設定不足・不正クレーム・DBエラーではメッセージと `st.stop()` で停止する。`logout() -> None` は状態を消して `st.logout()` を呼ぶ。

- [ ] モックしたStreamlit境界のテストを書く。未認証・設定不足ではユーザー作成が呼ばれず、ログインボタンはgoogleプロバイダを使うことを検証する。
- [ ] 正常な認証済みsubjectのユーザーID返却、欠落・非文字列・空白subjectの拒否、Google以外のissuerの拒否を検証する。許可issuerは `https://accounts.google.com` と `accounts.google.com`。
- [ ] 主体変更時とログアウト時に回答入力・選択状態が消えること、同一主体のrerunでは保持されることを検証する。
- [ ] DBエラーで停止し、例外詳細・秘密値を画面に表示しないことを検証する。
- [ ] `PYTHONPATH=src python3 -m pytest tests/auth/test_oidc.py -q` で失敗を確認する。
- [ ] require_google_loginを小さな設定確認・クレーム取得・状態管理の関数に分けて実装する。認証主体が確定してからTask 1のユーザー登録を呼ぶ。
- [ ] 設定例にはplaceholderのみを記載し、実secrets.tomlをgitignoreに追加する。
- [ ] 両依存ファイルに `streamlit[auth]>=1.45.0` を指定し、Python要件を `>=3.10` にする。pre-commitのpylint環境にも同じStreamlit要件を反映する。
- [ ] 不足する検証用依存はプロジェクト用仮想環境へ導入する。ネットワーク制限で失敗した場合は必要なコマンドの承認を要求する。
- [ ] 認証モジュールのテストを再実行し、成功を確認する。

### Task 4: 全タブへの認証済みユーザーIDの接続

**Files:** Modify `src/app.py`, `src/frontend/core.py`, `src/frontend/tab1_search.py`, `src/frontend/tab4_favorite.py`, `src/frontend/tab6_wordcard.py`, `src/frontend/tab8_sentence_composition.py`, `tests/backend/test_sentence_composition_ui.py`; create `tests/auth/test_app_auth.py`, `tests/backend/test_user_vocabulary_ui.py`.

**Interfaces:** 検索・お気に入り・カード・英作文の `render(user_id: str) -> None`; `show_word_entry(word_id: int, user_id: str) -> None`; `show_status(word: str, prefix: str, user_id: str) -> None`; `show_favorite(word: str, prefix: str, user_id: str) -> None`。一覧表示だけのバッチタブは現行renderを維持する。

- [ ] アプリの認証境界とタブをモックし、未認証では全タブ・DB処理が呼ばれず、認証済みIDが4つの対象タブへ渡ることを検証する。
- [ ] AppTestと一時DBで、異なるタブprefixの同じ単語の表示がキー衝突せず、操作が対象ユーザーへ保存されることを検証する。
- [ ] 英作文UIテストを明示的なテストユーザーIDに変更し、別ユーザーで同じ画面を開くと回答履歴が空であることを追加検証する。
- [ ] 関連テストを実行して新しい引数・認証制御の欠落による失敗を確認する。
- [ ] app.pyの先頭で認証を行い、固定USER_IDを除去して各タブへIDを渡す。共通の状態・お気に入りのキーはprefixとuser_idとwordを含める。
- [ ] 対象タブから共通部品、共通部品からTask 2の関数へIDを渡す。英作文renderのデフォルトユーザーを除去する。
- [ ] ユーザー状態の読み書きでDBエラーが起きた場合に制御されたメッセージで停止する。共有データへフォールバックしない。
- [ ] 既存 `tests/backend/test_practice_history.py` を含めて関連テストを実行し、成功を確認する。

### Task 5: APIの保護、設定ドキュメント、最終検証

**Files:** Modify `src/api.py`, `README.md`; create `tests/auth/test_api_auth.py`, `docs/google-auth.md`.

**Interfaces:** `GET /api/favorites` は常に403で、個人データを返さない。StreamlitログインがFastAPIを認証しないことを明示する。

- [ ] FastAPI TestClientで通常リクエストと任意user_id付きリクエストがともに403で、お気に入り取得を呼ばないテストを書く。
- [ ] `PYTHONPATH=src python3 -m pytest tests/auth/test_api_auth.py -q` で失敗を確認する。
- [ ] APIをHTTPExceptionの403応答へ変更し、不要なバックエンド呼び出しを除去する。
- [ ] docs/google-auth.mdにGoogle Cloudの同意画面・公開設定、Web OAuthクライアント、callback URL、srcからの起動、設定例コピー、秘密値管理、USER_DB_PATHの永続保存先、旧データ保持と後日の引き継ぎを記載する。READMEからリンクする。
- [ ] 実Googleログイン・キャンセル・ログアウト・別アカウント利用・本番callbackの手動確認手順を記載し、実設定なしでは未検証とする。
- [ ] `PYTHONPATH=src python3 -m pytest tests/backend tests/auth -q` を実行し、全件成功を確認する。
- [ ] `pre-commit run --all-files` を実行する。今回の変更による失敗を修正し、既存の失敗は発生箇所と理由を区別して報告する。
- [ ] `git diff --check` と `git status --short` を確認し、DB差分・実秘密値が含まれないことを確認する。
- [ ] 独立レビューまたは自己レビューで全SQLのuser_id条件と未認証時の停止順序を確認する。レビュー手段は承認された実行方式に従う。
- [ ] コミットが必要な場合は全体pre-commitが成功してから日本語メッセージを使う。失敗したままコミットしない。
- [ ] 完了報告に実装箇所、実行した検証結果、Google側で残る設定と未検証事項を記載する。

## 実行結果（2026-10-03）

Task 1–5の実装を完了。対象テスト32件、変更ファイルのpre-commit全フック、独立レビュー、git diff --checkを確認済み。実DBの差分なし。

全体pytestは既存CLIのspellchecker依存不足で収集に失敗。全体pre-commitは既存パイプライン・スクリプトの型/lintエラーで失敗。コミット・マージは行っていない。Googleの実設定と実アカウントによるcallback検証は未実施。

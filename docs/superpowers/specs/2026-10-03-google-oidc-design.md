# Google OIDC認証とユーザー別学習データ

## 合意した目的

現行StreamlitアプリにGoogleアカウントによるログインを追加する。個人利用が中心だが、Googleアカウントを持つ誰でも利用できる。お気に入り、習得状態、瞬間英作文の履歴をユーザーごとに分離する。既存データの個人アカウントへの引き継ぎは後日行う。認証コードは独立したファイルにまとめ、責務が読み取れる構成にする。

## 採用方式

Streamlit標準の `st.login("google")`、`st.logout()`、`st.user` を使用する。OIDCのリダイレクト、IDトークン検証、state/nonce、認証CookieはStreamlitとAuthlibに任せる。独自のOAuthコールバックやトークン保存は実装しない。

比較したバックエンド主導の認証はReact移行時に有用だが、今回のStreamlit向け実装では追加のセッション連携が必要になる。外部認証サービスの導入も今回のGoogle単独ログインには不要である。

## ファイルと責務

- `src/auth/__init__.py`：認証パッケージ。
- `src/auth/oidc.py`：Googleログイン画面、設定確認、認証必須の制御、認証済みクレームからの識別情報取得、ログアウト。未認証・設定不足・不正な識別情報では学習画面を実行しない。
- `src/backend/users.py`：ユーザーテーブル初期化とGoogle subjectから内部ユーザーIDへの変換。Streamlitへの依存を持たない。
- `src/backend/core/user_schema.py`：ユーザー別お気に入り・習得状態の追加テーブル初期化。既存テーブルを変更しない。
- `src/app.py`：認証を先に実行し、取得したユーザーIDをタブへ明示的に渡す。固定の `default_user` を使用しない。
- `src/backend/favorite.py`、`vocab_status.py`：ユーザーIDを必須引数にし、全クエリをユーザーで絞り込む。
- `src/frontend/core.py` と検索・お気に入り・カードのタブ：ユーザーIDをバックエンドまで渡す。共通ウィジェットのキーにはタブとユーザーの識別を含める。
- `src/frontend/tab8_sentence_composition.py`：認証済みユーザーIDを必須にする。既存の回答・自己評価・再挑戦の仕組みを利用する。
- `src/.streamlit/secrets.toml.example`：秘密値を含まない設定例。
- `docs/google-auth.md` とREADME：Google Cloud、ローカル起動、本番設定、旧データの保持方法、検証方法を説明する。

## ユーザー識別とDB

Googleから得た `sub` をメールアドレスと独立した永続識別子として使う。`users` テーブルで `UNIQUE(provider, subject)` と内部 `user_id`（UUID）を管理する。表示名は表示目的に限定し、メールアドレスによる既存データの自動引き継ぎはしない。

アプリ本体のユーザDBに以下を追加する。パイプラインの `instance/words.db` は変更しない。

- `users(user_id PRIMARY KEY, provider, subject, UNIQUE(provider, subject))`
- `user_favorites(user_id, word, PRIMARY KEY(user_id, word))`
- `user_vocab_status(user_id, word, status, PRIMARY KEY(user_id, word))`

新規テーブルのユーザーIDは `users` を参照し、接続で外部キー制約を有効にする。習得状態には従来と同じCHECK制約を付ける。初期化は繰り返し可能にし、ユーザー作成は同時ログインでも一意性を維持する。

旧 `favorites`、`vocab_status` と `default_user` の練習履歴・評価は保持し、新しいユーザーから読み出さない。新規アカウントはお気に入りなし、習得状態unknown、履歴なしで始める。後日の引き継ぎで旧テーブルから指定アカウントへのコピーと、旧履歴の所有者更新が可能な構造を残す。引き継ぎコマンドの実装は今回含めない。

辞書DBの内容と全体検索回数の扱いは維持する。共有辞書はユーザー別に複製しない。

## セッションとアクセス制御

認証を完了するまではタブ描画、ユーザーDB初期化、検索処理を実行しない。ログアウト時および認証主体の変更時には画面のセッション状態をクリアし、別アカウントの回答入力・学習状態が残らないようにする。ユーザーIDはフォーム入力やURLから受け取らない。

現在のFastAPI `/api/favorites` は認証がなく、StreamlitのCookieもそのままAPI認証には使えない。このエンドポイントは今回、ユーザーデータを返さない403応答に変更する。React/API向け認証は後日の対象とし、この仕様変更をドキュメントに記載する。

## 設定と運用

`[auth]` にredirect URIとCookie署名秘密値、`[auth.google]` にclient ID、client secret、Google discovery URLを設定する。スコープは `openid profile email` とする。秘密値の実ファイルはgitignoreに追加し、ログ・画面に露出させない。

依存は `pyproject.toml` と `requirements.txt` の両方で `streamlit[auth]` と `st.user` が使える下限バージョンを指定する。Python要件は実装と依存が対応する3.10以上に揃える。pre-commitの追加依存も整合させる。

Google Cloud側ではWeb applicationのOAuthクライアントと同意画面を用意し、ローカル `http://localhost:8501/oauth2callback` と本番HTTPSのcallbackを登録する。一般ユーザー向けに公開する際はGoogle側の公開設定も行う。

本番のユーザDBは `USER_DB_PATH` でリポジトリ外の永続保存先を指定し、既存データを保持したい場合は起動前にそこへコピーする。これはアカウントへの引き継ぎとは別の保存先設定である。開発中は実DBを変更せず、一時DBで検証する。

## エラー処理

OIDC設定不足ではセットアップが必要であることを表示して停止する。ログイン状態でもGoogle subjectが欠落・不正な場合は停止し、再ログインを案内する。DBエラーではユーザー向けメッセージを表示して停止し、共有データや `default_user` へのフォールバックは行わない。

## 検証と受け入れ条件

一時DBを用いて、同一subjectのユーザーID安定性、異なるアカウントの分離、旧データの保持、初期化の再実行、同じ単語の独立したお気に入り・状態変更を確認する。既存の英作文履歴テストも実行する。

認証境界をモックしたStreamlitのテストで、未ログイン時の処理停止、設定不足、不正なクレーム、ログアウト・アカウント変更時の状態クリア、各タブへのユーザーID受け渡しを確認する。APIの403応答も確認する。

適切なPythonで対象テストとpre-commitを実行し、既存の全体チェックに失敗がある場合は今回の変更によるものかを区別して報告する。git差分に実DB・秘密値が含まれないことを確認する。

実Googleアカウントでのログイン・キャンセル・ログアウト・別アカウント利用、本番callbackの検証にはGoogle Cloudの実設定が必要であり、モックテストの結果とは分けて報告する。今回、外部プロジェクト作成や本番デプロイは行わない。

## 参照

- https://docs.streamlit.io/develop/api-reference/user/st.login
- https://docs.streamlit.io/develop/api-reference/user/st.user
- https://docs.streamlit.io/develop/tutorials/authentication/google
- https://developers.google.com/identity/openid-connect/openid-connect

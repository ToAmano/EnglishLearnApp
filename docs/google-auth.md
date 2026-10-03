# Googleログインの設定

現行UIはGoogleアカウントでのログインが必須です。認証の入り口は `src/auth/oidc.py`、ユーザー識別は `src/backend/users.py`、追加DBスキーマは `src/backend/core/user_schema.py` に分離しています。

## ローカル環境

Python 3.10以上で依存をインストールしてください。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp src/.streamlit/secrets.toml.example src/.streamlit/secrets.toml
```

Google Cloud Consoleでプロジェクトを選び、Google Auth Platformを設定します。

1. Brandingでアプリ名と連絡先など同意画面の情報を登録します。
2. Audienceを一般のGoogleアカウントが使えるExternalに設定します。開発中のTestingでは利用するアカウントをテストユーザーに登録してください。
3. ClientsでWeb applicationのOAuthクライアントを作成します。
4. Authorized redirect URIsに `http://localhost:8501/oauth2callback` を登録します。
5. 発行したclient IDとclient secretを `src/.streamlit/secrets.toml` の `[auth.google]` に設定します。
6. `[auth]` のcookie_secretを十分に長いランダム文字列へ置き換えます。例：`python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`。

設定例の `REPLACE_WITH_...` は実際の値に置き換えてください。実secrets.tomlはGitの対象外です。秘密値をREADME、チャット、ログ、コミットに貼り付けないでください。

```bash
cd src
streamlit run app.py
```

`localhost` と `127.0.0.1`、ポート番号はcallback設定と一致させてください。起動ディレクトリは `src/` です。認証設定がない場合は設定案内で停止し、学習画面やDB処理を実行しません。

## 保存データ

Googleの永続識別子subを内部UUIDへ対応付けます。メールアドレスが変わっても同じsubjectなら同じユーザーです。新しいアカウントはお気に入りなし・習得状態unknown・英作文履歴なしで開始します。

- 新しいお気に入りは `user_favorites`、習得状態は `user_vocab_status` に保存します。
- 旧 `favorites` と `vocab_status` は保持し、新規アカウントからは参照しません。
- `default_user` の英作文履歴・自己評価も保持します。新規アカウントには自動移行しません。
- 後日の引き継ぎでは、指定アカウントへ旧データをコピーし、旧履歴の所有者を更新できます。引き継ぎ操作は今回の実装に含めていません。
- 辞書DBの検索回数は全ユーザー共通の統計です。

## 本番環境

Google側へ `https://<公開ホスト>/oauth2callback` を追加し、アプリ側のredirect_uriにも同じURLを設定します。秘密値はサーバー側の秘密設定から `src/.streamlit/secrets.toml` へ供給してください。全インスタンスで同じcookie_secretを使います。Googleアカウントがあれば誰でも利用できる公開状態にする際は、Google Auth PlatformのAudienceで公開設定も行います。

GitHub Actionsは `startup.sh` でStreamlitを起動します。ユーザーDBのデフォルト保存先は `/home/data/EnglishLearnApp/user.db` です。初回のみ同梱の旧DBをコピーし、以後のデプロイでは永続DBを上書きしません。

Azure PortalのApp Service「Environment variables（環境変数）」に次を設定すると、起動時にOIDC設定ファイルを生成できます。

| 変数 | 設定値 |
|---|---|
| `OIDC_CLIENT_ID` | Googleのclient ID |
| `OIDC_CLIENT_SECRET` | Googleのclient secret |
| `OIDC_COOKIE_SECRET` | 固定の長いランダム文字列 |
| `OIDC_REDIRECT_URI` | `https://<公開ホスト>/oauth2callback`（省略時はAzureのWEBSITE_HOSTNAMEから生成） |

保存してApp Serviceを再起動してください。Google側にも同じcallback URLを登録します。秘密値はGitHubへコミットしません。認証の3つの必須変数が未設定なら、公開後も設定案内画面で停止します。

本番の `USER_DB_PATH` はリポジトリ外の永続保存先に設定してください。デプロイ成果物の `src/database/user.db` を稼働用に使うと、再デプロイ時にデータを失う可能性があります。既存データを残したい場合は、初回起動前にバックアップし、そのDBを永続保存先へコピーしてからUSER_DB_PATHを設定します。この保存先の変更と、個人アカウントへのデータ引き継ぎは別の操作です。

SQLiteを使用するため、まず単一アプリインスタンスで運用してください。複数インスタンスの共有保存先とDB構成は別途検討が必要です。

## React / FastAPIについて

StreamlitのログインはFastAPIを認証しません。API向け認証を導入するまでは `/api/favorites` は403を返し、Reactのお気に入り画面から取得できません。URLにuser_idを渡すだけでは利用できません。

## 動作確認

一時DBを使った自動テストをリポジトリルートで実行できます。APIテストにはFastAPIとhttpxが必要です（pyproject.tomlのFastAPI依存に加え、`pip install httpx`）。

```bash
PYTHONPATH=src python3 -m pytest tests/backend tests/auth -q
```

実Google認証は次の手順で別途確認してください。

1. 未ログインで学習画面が表示されないことを確認する。
2. Googleログインをキャンセルしても学習画面に入れないことを確認する。
3. アカウントAでログインし、お気に入り・習得状態・英作文回答を保存する。
4. ログアウト後、アカウントBでログインし、Aのデータと入力状態が見えないことを確認する。
5. Aで再ログインし、保存したデータが復元されることを確認する。
6. 本番URLで同じ操作を行い、callbackが成功することを確認する。

モックを使う自動テストは、Google側の同意画面・client secret・callback設定を検証しません。

Streamlitのログアウトはアプリのログイン状態を解除します。Googleアカウントそのものからはログアウトしません。標準認証Cookieの保持期間は30日です。別タブで既に開いているセッションは、そのタブでログアウトするまで認証状態を保持する場合があります。全セッションを一括失効する機能は今回含めていません。

## 公式資料

- [StreamlitのGoogle認証チュートリアル](https://docs.streamlit.io/develop/tutorials/authentication/google)
- [st.login](https://docs.streamlit.io/develop/api-reference/user/st.login)
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)

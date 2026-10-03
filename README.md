# EnglishLearnApp

Streamlitによる英日辞書・語彙学習・瞬間英作文アプリです。

Googleアカウントでログインし、お気に入り・習得状態・回答履歴をユーザー別に保存します。

[Googleログインの設定と起動手順](docs/google-auth.md)を参照してください。認証設定の例は `src/.streamlit/secrets.toml.example` です。

OIDC認証は `src/auth/oidc.py`、ユーザー識別は `src/backend/users.py` に分離しています。旧データは保持し、アカウントへの引き継ぎは後日行えます。

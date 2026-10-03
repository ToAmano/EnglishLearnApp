"""Google OIDCログイン。トークン検証とCookie管理はStreamlitに委譲する。"""

import sqlite3
from collections.abc import Mapping
from typing import NoReturn

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from backend import users

GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
SESSION_USER_KEY = "oidc_user_id"


def _stop_with_error(message: str) -> NoReturn:
    st.error(message)
    st.stop()
    # 型情報のない検証環境でもNoReturnを明示する。通常はst.stopが先に終了する。
    # pylint: disable-next=unreachable
    raise RuntimeError("Streamlit did not stop execution")


def _configured() -> bool:
    try:
        settings = st.secrets["auth"]
        provider = settings["google"]
        values = (
            settings["redirect_uri"],
            settings["cookie_secret"],
            provider["client_id"],
            provider["client_secret"],
        )
        return (
            all(isinstance(value, str) and bool(value.strip()) for value in values)
            and provider["server_metadata_url"] == GOOGLE_METADATA_URL
        )
    except (KeyError, TypeError, StreamlitSecretNotFoundError):
        return False


def _google_subject(claims: Mapping[str, object]) -> str:
    subject = claims.get("sub")
    if claims.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
        raise ValueError("Googleの認証情報ではありません。")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Googleのユーザー識別子がありません。")
    return subject


def logout() -> None:
    """学習画面の状態を消してから認証Cookieを削除する。"""
    st.session_state.clear()
    st.logout()


def require_google_login() -> str:
    """未認証なら画面を停止し、認証済みなら内部ユーザーIDを返す。"""
    if not _configured():
        st.session_state.clear()
        _stop_with_error(
            "Googleログインの設定が必要です。docs/google-auth.md の手順を確認してください。"
        )
    if not st.user.is_logged_in:
        st.session_state.clear()
        st.header("📖 英語学習アプリ")
        st.button("Googleでログイン", on_click=st.login, args=("google",))
        st.stop()
    try:
        subject = _google_subject(st.user)
        user_id = str(users.get_or_create_google_user(subject))
    except ValueError:
        st.session_state.clear()
        st.button("ログアウトしてやり直す", on_click=logout)
        _stop_with_error("認証情報を確認できませんでした。再ログインしてください。")
    except sqlite3.Error:
        _stop_with_error("学習データを開けませんでした。DBの設定を確認してください。")
    if st.session_state.get(SESSION_USER_KEY) != user_id:
        st.session_state.clear()
        st.session_state[SESSION_USER_KEY] = user_id
    with st.sidebar:
        st.write("Googleでログインしています")
        st.button("ログアウト", on_click=logout, key="oidc_logout")
    return user_id

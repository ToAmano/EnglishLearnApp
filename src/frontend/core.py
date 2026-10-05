import sqlite3

import streamlit as st

from backend.explanation import get_explanation
from backend.favorite import is_favorited, toggle_favorite
from backend.vocab_status import get_vocab_status, set_vocab_status
from frontend.speech import render_speech


def _save_status(word: str, user_id: str, key: str) -> None:
    try:
        set_vocab_status(word, str(st.session_state[key]), user_id)
    except sqlite3.Error:
        st.error("習得状態を保存できませんでした。DBの設定を確認してください。")
        st.stop()


def show_status(word: str, prefix: str, user_id: str) -> None:
    status = get_vocab_status(word, user_id)
    key = f"{prefix}_{user_id}_vocab_status_{word}"
    # DBの値を各タブに反映し、保存は操作したウィジェットのcallbackのみで行う。
    st.session_state[key] = status
    st.selectbox(
        "📘 単語の習得状態を選択",
        ["unknown", "passive", "active"],
        key=key,
        on_change=_save_status,
        args=(word, user_id, key),
        help="この単語の習得状態を選択してください。",
    )


def show_favorite(word: str, prefix: str, user_id: str) -> None:
    """呼び出し元とアカウントごとにキーを分ける。"""
    _, col2 = st.columns([4, 1])
    with col2:
        favorited = is_favorited(word, user_id)
        label = "⭐" if favorited else "☆"
        help_text = "お気に入り解除" if favorited else "お気に入り追加"
        if st.button(label, key=f"{prefix}_{user_id}_favorite_{word}", help=help_text):
            toggle_favorite(word, user_id)
            st.rerun()


def render_speak_button(word: str, autoplay: bool = False) -> None:
    """英語音声の選択と試聴。"""
    render_speech(word, autoplay)


def render_explanation(word_id: int) -> None:
    """単語の説明をMarkdownで表示"""
    with st.expander("詳細を見る"):
        explanation_md = get_explanation(word_id)
        if explanation_md:
            st.markdown(explanation_md, unsafe_allow_html=True)

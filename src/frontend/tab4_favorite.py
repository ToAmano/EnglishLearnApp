from typing import List

import streamlit as st

from backend.core.db_core import get_wordid_from_word
from backend.favorite import get_favorites_words
from frontend.core import (
    render_explanation,
    render_speak_button,
)


def go_prev() -> None:
    """Go to the previous word in favorites."""
    if st.session_state["favorite_card_index"] > 0:
        st.session_state["favorite_card_index"] -= 1


def go_next(num_favorites: int) -> None:
    """Go to the next word in favorites."""
    if st.session_state["favorite_card_index"] < num_favorites - 1:
        st.session_state["favorite_card_index"] += 1


def render() -> None:
    """Renders the favorite words tab with a card-like interface."""
    st.subheader("お気に入りの単語")

    favorite_words: List[str] = sorted(get_favorites_words())
    num_favorites = len(favorite_words)

    if (
        "favorite_card_index" not in st.session_state
        or st.session_state["favorite_card_index"] >= num_favorites
    ):
        st.session_state["favorite_card_index"] = 0

    if not favorite_words:
        st.info("お気に入りの単語はまだありません。")
        return

    card_index = st.session_state["favorite_card_index"]
    word = favorite_words[card_index]
    word_id = get_wordid_from_word(word)

    st.write(f"📌 **{word}** (ID: {word_id})")
    render_speak_button(word)
    render_explanation(word_id)

    # Navigation
    col1, _, col3 = st.columns([1, 3, 1])
    with col1:
        st.button(
            "⬅️ 前へ",
            key="prev_favorite_card",
            on_click=go_prev,
            disabled=(card_index <= 0),
        )
    with col3:
        st.button(
            "➡️ 次へ",
            key="next_favorite_card",
            on_click=go_next,
            args=(num_favorites,),
            disabled=(card_index >= num_favorites - 1),
        )

    st.caption(f"{card_index + 1} / {num_favorites}")

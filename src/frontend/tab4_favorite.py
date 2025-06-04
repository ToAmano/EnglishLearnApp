import streamlit as st

from backend.core.db_core import get_wordid_from_word
from backend.favorite import get_favorites


def render() -> None:
    st.subheader("お気に入りの単語")
    favorites: list[str] = get_favorites()
    if favorites:
        for word in favorites:
            word_id: int = get_wordid_from_word(word)
            st.write(f"📌 **{word}** {word_id}")
    else:
        st.info("お気に入りの単語はまだありません。")

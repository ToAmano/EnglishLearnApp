import streamlit as st

from backend.backend import get_favorites


def render() -> None:
    st.subheader("お気に入りの単語")
    favorites = get_favorites()
    if favorites:
        for row in favorites:
            st.write(f"📌 {row['word_id']} **{row['word']}**")
    else:
        st.info("お気に入りの単語はまだありません。")

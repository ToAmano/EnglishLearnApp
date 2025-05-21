from collections import defaultdict

import pandas as pd
import streamlit as st

from backend.backend import (
    get_derived_words,
    get_examples,
    get_synonyms,
    search_meanings,
)
from backend.core.db_core import get_word_from_wordid, get_wordid_from_word
from backend.search_count import get_search_count
from frontend.core import (
    render_explanation,
    render_speak_button,
    show_favorite,
    show_status,
    speak_word_automatically,
)


def show_word_entry(word_id: int) -> None:
    """詳細説明の表示 (一時的に先頭に表示)"""
    word: str = get_word_from_wordid(word_id)
    search_count: int = get_search_count(word_id)
    show_status(word)  # 単語の状態表示

    st.markdown(f"### 🔤 {word}")
    st.caption(f" word_id: {word_id} /検索回数: {search_count}")
    # 自動読み上げ用のJSコードを埋め込み
    speak_word_automatically(word)

    # --- 音声読み上げボタン（Web Speech API）
    render_speak_button(word)

    show_status(word)  # 単語の状態表示
    show_favorite(word)  # お気に入りボタン

    render_explanation(word_id)

    # 以下がmeanings DBが完成した時に表示される内容
    df: pd.DataFrame = search_meanings(word_id)
    grouped = df.groupby("word_id")
    show_meaning(grouped)

    show_derived(word_id)  # 派生語の表示
    show_synonym(word_id)  # 類語表示
    show_example(word_id)  # 例文表示


def show_meaning(df_grouped: pd.DataFrame) -> None:
    for _, group in df_grouped:
        pronunciation = group.iloc[0].get("pronunciation", "")
        category = group.iloc[0].get("category", "")
        st.caption(f"カテゴリ: {category} / 発音: {pronunciation}")
        show_pos(df_grouped)


def show_pos(df_group: pd.DataFrame) -> None:
    # 品詞別表示
    pos_dict = defaultdict(list)
    for _, row in df_group.iterrows():
        pos_dict[row["part_of_speech"]].append(row["meaning"])

    for pos, meanings in pos_dict.items():
        st.markdown(f"#### {pos}")
        for i, meaning in enumerate(meanings, start=1):
            st.write(f"{i}. {meaning}")


def show_derived(word_id: int) -> None:

    derived = get_derived_words(word_id)
    if derived:
        st.markdown("### 📚 派生語")
        for dw in derived:
            st.markdown(f"- {dw['word_id']}: **{dw['word']}**")


def show_synonym(word_id: int) -> None:
    synonyms = get_synonyms(word_id)
    if synonyms:
        st.markdown("#### 🔗 類義語")
        for row in synonyms:
            st.markdown(f"- {row['word_id']}: **{row['word']}**")


def show_example(word_id: int) -> None:
    """例文表示"""
    example_df: pd.DataFrame = get_examples(word_id)
    if example_df.empty:
        return
    st.markdown("#### 🗣️ 例文")
    for _, row in example_df.iterrows():
        st.markdown(f"- {row['example']}")
        if row["audio_path"]:
            try:
                with open(row["audio_path"], "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
            except OSError as e:
                st.warning(f"音声再生できません: {e}")


def render() -> None:
    st.subheader("単語を検索")
    word = st.text_input("単語を入力", "", key="search_input")

    if st.button("検索", key=1):
        word_id = get_wordid_from_word(word)
        st.session_state["word_id"] = word_id
    if "word_id" in st.session_state:
        print(f"セッションに結果がある :: word_id = {st.session_state['word_id']}")
        word_id = st.session_state["word_id"]
        show_word_entry(word_id)

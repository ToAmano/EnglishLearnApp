import pandas as pd
import streamlit as st

from backend.learning import get_word_batch

BATCH_SIZE = 100  # 一度に読み込む単語数


def render() -> None:
    st.header("📘 単語バッチ確認モード")

    # --- データ取得（バッチ全体を一括取得）
    sort_mode = st.radio(
        "📚 単語の並び順",
        options=["ID順", "アルファベット順"],
        horizontal=True,
        key="sort_mode_batch",
    )
    start_index = st.number_input(
        "スタート位置", min_value=0, step=BATCH_SIZE, value=0, key="start_index_batch"
    )
    print(f"start_index = {start_index}")
    order_by = "word_id" if sort_mode == "ID順" else "word"

    if st.button("この範囲の単語を表示"):
        display_word_batch(start_index, order_by)


def display_word_batch(start_index: int, order_by: str) -> None:
    df = get_word_batch(start=start_index, limit=BATCH_SIZE, order_by=order_by)
    if df.empty:
        st.info("これ以上の単語はありません。")
        return

    for _, row in df.iterrows():
        display_word(row)


def display_word(row: pd.Series) -> None:
    st.markdown(f"### 🔤 {row['word']} ({row['part_of_speech']})")
    st.markdown(f"- 意味: {row['meaning']}")
    st.markdown(f"- カテゴリ: {row['category']}")
    st.markdown("---")

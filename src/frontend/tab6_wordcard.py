import streamlit as st

from backend.learning import get_word_batch
from backend.search_count import get_search_count
from frontend.core import (
    render_explanation,
    render_speak_button,
    show_favorite,
    show_status,
    speak_word_automatically,
)

BATCH_SIZE = 100  # 一度に読み込む単語数


# --- ボタン用のコールバック関数を定義
def go_prev() -> None:
    """Go previous word"""
    if st.session_state["card_index"] > 0:
        st.session_state["card_index"] -= 1
    else:
        st.session_state["card_index"] = 0


def go_next(df_length: int) -> None:
    """Go next word"""
    if st.session_state["card_index"] < df_length - 1:
        st.session_state["card_index"] += 1
    else:
        st.session_state["card_index"] = df_length - 1


def get_idx(card_idx: int, len_df: int) -> int:
    new_card_idx: int = card_idx
    if card_idx >= len_df:
        st.session_state["card_index"] = len_df - 1
        new_card_idx = len_df - 1
    elif card_idx < 0:
        st.session_state["card_index"] = 0
        new_card_idx = 0
    print(f"card_idx = {new_card_idx}")
    return new_card_idx


def render() -> None:
    st.title("🃏 単語カードモード")

    sort_mode = st.radio(
        "📚 単語の並び順",
        options=["ID順", "アルファベット順"],
        horizontal=True,
        key="sort_mode_card",
    )
    # --- データ取得（バッチ全体を一括取得）
    start_index = st.number_input(
        "スタート位置", min_value=0, step=BATCH_SIZE, value=0, key="start_index_card"
    )
    print(f"start_index = {start_index}")
    order_by = "word_id" if sort_mode == "ID順" else "word"
    word_df = get_word_batch(start=start_index, limit=BATCH_SIZE, order_by=order_by)

    # --- セッションステートで位置管理
    if "card_index" not in st.session_state:
        st.session_state["card_index"] = 0
    card_idx = st.session_state["card_index"]
    # --- 単語が存在する場合のみカード表示
    if word_df.empty:
        st.info("単語が見つかりませんでした。")
    else:
        card_idx = get_idx(card_idx, len(word_df))

        row = word_df.iloc[card_idx]
        word_id = int(row["word_id"])
        word: str = row["word"]
        search_count: int = get_search_count(word_id)

        # --- 単語カード表示
        with st.container():
            st.markdown("### 🔤 英単語カード")
            st.markdown(f"## **{row['word']}**")
            st.caption(f" word_id: {word_id} /検索回数: {search_count}")
            # 自動読み上げ用のJSコードを埋め込み
            speak_word_automatically(word)

            # --- 音声読み上げボタン（Web Speech API）
            render_speak_button(word)

            show_status(word, "tab6_")  # 単語状態の表示
            show_favorite(word)  # お気に入りボタン

            with st.expander("意味を見る"):
                st.write(f"- 意味: {row['meaning']}")
                st.write(f"- 品詞: {row['part_of_speech']}")
                st.write(f"- カテゴリ: {row['category']}")

            render_explanation(word_id)

        # --- ナビゲーションボタン
        col1, _, col3 = st.columns([1, 3, 1])
        with col1:
            st.button("⬅️ 前へ", key="prev_card", on_click=go_prev)
        with col3:
            st.button("➡️ 次へ", key="next_card", on_click=lambda: go_next(len(word_df)))
        st.caption(f" {card_idx + 1} / {len(word_df)} 単語中")
        print(f"card_idx = {card_idx}")

from collections import defaultdict

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from backend.backend import (
    get_derived_words,
    get_examples,
    get_favorites,
    get_synonyms,
    is_favorited,
    search_word,
    toggle_favorite,
)
from backend.core.db_core import get_word_from_wordid
from backend.explanation import get_explanation
from backend.learning import get_word_batch
from backend.search_count import get_search_count
from backend.vocab_status import get_vocab_status, set_vocab_status

# セッションIDで user_id を代用（本番ならログイン機能と連携）
USER_ID = "default_user"


# --- ボタン用のコールバック関数を定義
def go_prev():
    if st.session_state["card_index"] > 0:
        st.session_state["card_index"] -= 1
    else:
        st.session_state["card_index"] = 0


def go_next(df_length: int):
    if st.session_state["card_index"] < df_length - 1:
        st.session_state["card_index"] += 1
    else:
        st.session_state["card_index"] = df_length - 1


def show_word_entry(df: pd.DataFrame):
    if df.empty:
        st.warning("見つかりませんでした。")
        return

    grouped = df.groupby("word_id")

    for word_id, group in grouped:
        word = get_word_from_wordid(word_id)
        pronunciation = group.iloc[0].get("pronunciation", "")
        category = group.iloc[0].get("category", "")
        search_count = get_search_count(word_id)
        status = get_vocab_status(word)
        word_status_key: str = f"vocab_status_{word_id}"
        st.session_state.setdefault(
            word_status_key, status
        )  # セッションに初期値がなければ設定
        print(status)

        # UI 表示
        new_status = st.selectbox(
            "📘 単語の習得状態を選択",
            ["unknown", "passive", "active"],
            key=word_status_key,
            help="この単語の習得状態を選択してください。",
        )
        if new_status != status:
            set_vocab_status(word, new_status)
            st.success(f"「{word}」の語彙状態を「{new_status}」に更新しました！")

        st.markdown(f"### 🔤 {word}")
        st.caption(
            f"カテゴリ: {category} / 発音: {pronunciation} / 検索回数: {search_count}"
        )

        # お気に入りボタン
        col1, col2 = st.columns([4, 1])
        with col2:
            if is_favorited(word):
                if st.button("★ お気に入り解除", key=f"fav_remove_{word_id}"):
                    toggle_favorite(word)
                    st.rerun()
            else:
                if st.button("☆ お気に入り追加", key=f"fav_add_{word_id}"):
                    toggle_favorite(word)
                    st.rerun()

        # 詳細説明の表示
        explanation_md = get_explanation(word_id)
        if explanation_md:
            st.markdown(explanation_md, unsafe_allow_html=True)

        # 品詞別表示
        pos_dict = defaultdict(list)
        for _, row in group.iterrows():
            pos_dict[row["part_of_speech"]].append(row["meaning"])

        for pos, meanings in pos_dict.items():
            st.markdown(f"#### {pos}")
            for i, meaning in enumerate(meanings, start=1):
                st.write(f"{i}. {meaning}")

        # 派生語の表示
        derived = get_derived_words(word_id)
        if derived:
            st.markdown("### 📚 派生語")
            for dw in derived:
                st.markdown(f"- {dw['word_id']}: **{dw['word']}**")

        synonyms = get_synonyms(word_id)
        if synonyms:
            st.markdown("#### 🔗 類義語")
            for row in synonyms:
                st.markdown(f"- {row['word_id']}: **{row['word']}**")

        # 例文表示
        example_df = get_examples(word_id)
        if not example_df.empty:
            st.markdown("#### 🗣️ 例文")
            for i, row in example_df.iterrows():
                st.markdown(f"- {row['example']}")
                if row["audio_path"]:
                    try:
                        audio_file = open(row["audio_path"], "rb")
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.warning(f"音声再生できません: {e}")


# Streamlit UI
st.title("📖 英語辞書アプリ")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🔍 単語検索",
        "📝 単語テスト",
        "🔊 例文リスニング",
        "⭐ お気に入り",
        "📘 単語バッチ確認モード",
        "🃏 単語カードモード",
    ]
)

# 🔍 単語検索
with tab1:
    st.subheader("単語を検索")
    word = st.text_input("単語を入力", "", key="search_input")

    if st.button("検索", key=1):
        df_results = search_word(word)
        if not df_results.empty:
            st.session_state["search_result"] = df_results
        else:
            st.warning("見つかりませんでした。")
    if "search_result" in st.session_state:
        print(f"セッションに結果がある :: {st.session_state['search_result']}")
        df_results = st.session_state["search_result"]
        show_word_entry(df_results)

# 📝 単語テスト
with tab2:
    st.subheader("単語テスト（開発中）")

# 🔊 例文リスニング
with tab3:
    st.subheader("例文のリスニング（開発中）")

# ⭐ お気に入り
with tab4:
    st.subheader("お気に入りの単語")
    favorites = get_favorites()
    if favorites:
        for row in favorites:
            st.write(f"📌 {row['word_id']} **{row['word']}**")

    else:
        st.info("お気に入りの単語はまだありません。")

with tab5:
    st.header("📘 単語バッチ確認モード")

    # --- データ取得（バッチ全体を一括取得）
    sort_mode = st.radio(
        "📚 単語の並び順",
        options=["ID順", "アルファベット順"],
        horizontal=True,
        key="sort_mode_batch",
    )
    batch_size = 100  # 一度に読み込む単語数
    start_index = st.number_input(
        "スタート位置", min_value=0, step=batch_size, value=0, key="start_index_batch"
    )
    print(f"start_index = {start_index}")
    order_by = "word_id" if sort_mode == "ID順" else "word"

    if st.button("この範囲の単語を表示"):
        df = get_word_batch(start=start_index, limit=batch_size, order_by=order_by)
        if not df.empty:
            for idx, row in df.iterrows():
                st.markdown(f"### 🔤 {row['word']} ({row['part_of_speech']})")
                st.markdown(f"- 意味: {row['meaning']}")
                st.markdown(f"- カテゴリ: {row['category']}")
                st.markdown("---")
        else:
            st.info("これ以上の単語はありません。")


with tab6:
    st.title("🃏 単語カードモード")

    sort_mode = st.radio(
        "📚 単語の並び順",
        options=["ID順", "アルファベット順"],
        horizontal=True,
        key="sort_mode_card",
    )
    # --- データ取得（バッチ全体を一括取得）
    batch_size = 100  # 一度に読み込む単語数
    start_index = st.number_input(
        "スタート位置", min_value=0, step=batch_size, value=0, key="start_index_card"
    )
    print(f"start_index = {start_index}")
    order_by = "word_id" if sort_mode == "ID順" else "word"
    word_df = get_word_batch(start=start_index, limit=batch_size, order_by=order_by)

    # --- セッションステートで位置管理
    if "card_index" not in st.session_state:
        st.session_state["card_index"] = 0

    # word_df = get_word_batch(start=0, limit=batch_size)

    # --- 単語が存在する場合のみカード表示
    if not word_df.empty:
        card_idx = st.session_state["card_index"]
        if card_idx >= len(word_df):
            st.session_state["card_index"] = len(word_df) - 1
            card_idx = len(word_df) - 1
        elif card_idx < 0:
            st.session_state["card_index"] = 0
            card_idx = 0
        print(f"card_idx = {card_idx}")

        row = word_df.iloc[card_idx]
        word_id = int(row["word_id"])
        print(f"word_id = {word_id}")

        # --- 単語カード表示
        with st.container():
            st.markdown("### 🔤 英単語カード")
            st.markdown(f"## **{row['word']}**")
            # 自動読み上げ用のJSコードを埋め込み
            components.html(
                f"""
                <script>
                    const utterance = new SpeechSynthesisUtterance("{row['word']}");
                    utterance.lang = "en-US";
                    speechSynthesis.cancel();  // 前の発話が残っていたら中断
                    speechSynthesis.speak(utterance);
                </script>
            """,
                height=0,
            )  # 高さ0でボタンは表示しない

            # --- 音声読み上げボタン（Web Speech API）
            speech_html = f"""
                <button onclick="const u = new SpeechSynthesisUtterance('{row['word']}'); u.lang='en-US'; speechSynthesis.speak(u);">
                    🔊 発音を聞く
                </button>
            """
            components.html(speech_html, height=50)

            word = get_word_from_wordid(word_id)
            status = get_vocab_status(word)
            word_status_key_2: str = f"vocab_status_card_{word_id}"
            st.session_state.setdefault(
                word_status_key_2, status
            )  # セッションに初期値がなければ設定
            print(f"status = {status}")

            # UI 表示
            new_status = st.selectbox(
                "📘 単語の習得状態を選択",
                ["unknown", "passive", "active"],
                key=word_status_key_2,
                help="この単語の習得状態を選択してください。",
            )
            if new_status != status:
                print(f"new_status = {new_status}")
                set_vocab_status(word, new_status)
                st.success(f"「{word}」の語彙状態を「{new_status}」に更新しました！")

            # お気に入りボタン
            col1, col2 = st.columns([4, 1])
            with col2:
                if is_favorited(word):
                    if st.button("★ お気に入り解除", key=f"fav_remove_{word_id}"):
                        toggle_favorite(word)
                        st.rerun()
                else:
                    if st.button("☆ お気に入り追加", key=f"fav_add_{word_id}"):
                        toggle_favorite(word)
                        st.rerun()

            with st.expander("意味を見る"):
                st.write(f"- 意味: {row['meaning']}")
                st.write(f"- 品詞: {row['part_of_speech']}")
                st.write(f"- カテゴリ: {row['category']}")

            explanation_md = get_explanation(word_id)
            if explanation_md:
                with st.expander("📖 詳細な解説を読む"):
                    st.markdown(explanation_md, unsafe_allow_html=True)

        # --- ナビゲーションボタン
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.button("⬅️ 前へ", key="prev_card", on_click=go_prev)
        with col3:
            st.button("➡️ 次へ", key="next_card", on_click=lambda: go_next(len(word_df)))

        st.caption(f"{card_idx+1} / {len(word_df)} 単語中")
        print(f"card_idx = {card_idx}")
    else:
        st.info("単語が見つかりませんでした。")

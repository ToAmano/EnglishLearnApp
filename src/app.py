from collections import defaultdict

import streamlit as st

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
from backend.search_count import get_search_count
from backend.vocab_status import get_vocab_status, set_vocab_status

# セッションIDで user_id を代用（本番ならログイン機能と連携）
USER_ID = "default_user"


def show_word_entry(df):
    if df.empty:
        st.warning("見つかりませんでした。")
        return

    grouped = df.groupby("word_id")

    for word_id, group in grouped:
        word = get_word_from_wordid(word_id)
        pronunciation = group.iloc[0].get("pronunciation", "")
        category = group.iloc[0].get("category", "")
        search_count = get_search_count(word_id)
        status = get_vocab_status(word_id)
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
            set_vocab_status(word_id, new_status)
            st.success(f"「{word}」の語彙状態を「{new_status}」に更新しました！")

        st.markdown(f"### 🔤 {word}")
        st.caption(
            f"カテゴリ: {category} / 発音: {pronunciation} / 検索回数: {search_count}"
        )

        # お気に入りボタン
        col1, col2 = st.columns([4, 1])
        with col2:
            if is_favorited(word_id):
                if st.button("★ お気に入り解除", key=f"fav_remove_{word_id}"):
                    toggle_favorite(word_id)
                    st.rerun()
            else:
                if st.button("☆ お気に入り追加", key=f"fav_add_{word_id}"):
                    toggle_favorite(word_id)
                    st.rerun()

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

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔍 単語検索", "📝 単語テスト", "🔊 例文リスニング", "⭐ お気に入り"]
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

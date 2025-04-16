import streamlit as st
from collections import defaultdict
from backend.backend import search_word,get_favorites,get_examples,is_favorited,toggle_favorite,get_derived_words,get_synonyms
from backend.core.db_core import get_word_from_wordid
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

        st.markdown(f"### 🔤 {word}")
        st.caption(f"カテゴリ: {category} / 発音: {pronunciation}")

        # お気に入りボタン
        col1, col2 = st.columns([4, 1])
        with col2:
            if is_favorited(word_id):
                if st.button("★ お気に入り解除", key=f"fav_remove_{word_id}"):
                    toggle_favorite(word_id)
                    st.experimental_rerun()
            else:
                if st.button("☆ お気に入り追加", key=f"fav_add_{word_id}"):
                    toggle_favorite(word_id)
                    st.experimental_rerun()

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
            print(derived)
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
                if row['audio_path']:
                    try:
                        audio_file = open(row['audio_path'], 'rb')
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format='audio/mp3')
                    except Exception as e:
                        st.warning(f"音声再生できません: {e}")

# Streamlit UI
st.title("📖 英語辞書アプリ")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 単語検索", "📝 単語テスト", "🔊 例文リスニング", "⭐ お気に入り"])

# 🔍 単語検索
with tab1:
    st.subheader("単語を検索")
    word = st.text_input("単語を入力", "")

    if st.button("検索",key=1):
        results = search_word(word)
        show_word_entry(results)


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
            st.write(f"📌 **{row['word']}**: {row['meaning']}")

            # # お気に入り削除ボタン
            # if st.button(f"❌ {row['word']} をお気に入りから削除", key=f"del_{row['word_id']}"):
            #     remove_favorite(row['word_id'])
            #     st.success("お気に入りから削除しました！")

    else:
        st.info("お気に入りの単語はまだありません。")
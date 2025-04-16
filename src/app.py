import streamlit as st
import sqlite3
import pandas as pd
from collections import defaultdict
import base64
import io

# セッションIDで user_id を代用（本番ならログイン機能と連携）
USER_ID = "default_user"


# データベース接続関数
def get_db_connection():
    conn = sqlite3.connect("database/words.db")
    conn.row_factory = sqlite3.Row
    return conn

# 単語検索機能
def search_word(word):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM words WHERE word=?", (word,))
    results = cursor.fetchall()
    df = pd.read_sql_query("SELECT * FROM words WHERE word LIKE ?", conn, params=(word,))
    conn.close()
    return df # results

def get_examples(word_number):
    conn = get_db_connection()
    #    cursor.execute("SELECT * FROM examples WHERE word_number=?", (word_number,))
    df = pd.read_sql_query("SELECT * FROM examples WHERE word_number=?", conn, params=(word_number,))
    conn.close()
    return df

def is_favorited(word_number: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM favorites WHERE word_number = ?",
        (word_number,)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def toggle_favorite(word_number: int):
    conn = get_db_connection()
    cur = conn.cursor()
    if is_favorited(word_number):
        cur.execute(
            "DELETE FROM favorites WHERE word_number = ?",
            (word_number,)
        )
    else:
        cur.execute(
            "INSERT INTO favorites (word_number) VALUES (?)",
            (word_number,)
        )
    conn.commit()
    conn.close()

def show_word_entry(df):
    if df.empty:
        st.warning("見つかりませんでした。")
        return

    grouped = df.groupby("word_number")

    for word_number, group in grouped:
        word = group.iloc[0]["word"]
        pronunciation = group.iloc[0].get("pronunciation", "")
        category = group.iloc[0].get("category", "")

        st.markdown(f"### 🔤 {word}")
        st.caption(f"カテゴリ: {category} / 発音: {pronunciation}")

        # お気に入りボタン
        col1, col2 = st.columns([4, 1])
        with col2:
            if is_favorited(word_number):
                if st.button("★ お気に入り解除", key=f"fav_remove_{word_number}"):
                    toggle_favorite(word_number)
                    st.experimental_rerun()
            else:
                if st.button("☆ お気に入り追加", key=f"fav_add_{word_number}"):
                    toggle_favorite(word_number)
                    st.experimental_rerun()

        # 品詞別表示
        pos_dict = defaultdict(list)
        for _, row in group.iterrows():
            pos_dict[row["part_of_speech"]].append(row["meaning"])

        for pos, meanings in pos_dict.items():
            st.markdown(f"#### {pos}")
            for i, meaning in enumerate(meanings, start=1):
                st.write(f"{i}. {meaning}")

        # 例文表示
        example_df = get_examples(word_number)
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

# お気に入りリスト取得
def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM words WHERE word_number IN (SELECT word_number FROM favorites)")
    favorites = cursor.fetchall()
    conn.close()
    return favorites

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
            # if st.button(f"❌ {row['word']} をお気に入りから削除", key=f"del_{row['word_number']}"):
            #     remove_favorite(row['word_number'])
            #     st.success("お気に入りから削除しました！")

    else:
        st.info("お気に入りの単語はまだありません。")
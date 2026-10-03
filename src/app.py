"""Entry point
To run the App,

```bash
streamlit run app.py
```

"""

import sqlite3

import streamlit as st
from dotenv import load_dotenv

from auth.oidc import require_google_login
from frontend import (
    tab1_search,
    tab4_favorite,
    tab5_wordbatch,
    tab6_wordcard,
    tab8_sentence_composition,
)

load_dotenv()

USER_ID = require_google_login()


try:
    # Streamlit UI
    st.title("📖 英語辞書アプリ")

    tab1, tab2, tab3, tab4, tab5, tab6, tab8 = st.tabs(
        [
            "🔍 単語検索",
            "📝 単語テスト",
            "🔊 例文リスニング",
            "⭐ お気に入り",
            "📘 単語バッチ確認モード",
            "🃏 単語カードモード",
            "✍️ 瞬間英作文",
        ]
    )

    # 🔍 単語検索
    with tab1:
        tab1_search.render(USER_ID)

    # 📝 単語テスト
    with tab2:
        st.subheader("単語テスト（開発中）")

    # 🔊 例文リスニング
    with tab3:
        st.subheader("例文のリスニング（開発中）")

    # お気に入りタブには未解決のバグが残っていそう
    with tab4:
        tab4_favorite.render(USER_ID)
    with tab5:
        tab5_wordbatch.render()
    with tab6:
        tab6_wordcard.render(USER_ID)

    with tab8:
        tab8_sentence_composition.render(USER_ID)
except sqlite3.Error:
    st.error("学習データの読み書きに失敗しました。DBの設定を確認してください。")
    st.stop()

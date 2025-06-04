"""Entry point
To run the App,

```bash
streamlit run app.py
```

"""

import streamlit as st
from dotenv import load_dotenv

from frontend import tab1_search, tab4_favorite, tab5_wordbatch, tab6_wordcard

load_dotenv()

# セッションIDで user_id を代用（本番ならログイン機能と連携）
USER_ID = "default_user"


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
    tab1_search.render()

# 📝 単語テスト
with tab2:
    st.subheader("単語テスト（開発中）")

# 🔊 例文リスニング
with tab3:
    st.subheader("例文のリスニング（開発中）")

# ⭐ お気に入り
with tab4:
    tab4_favorite.render()
with tab5:
    tab5_wordbatch.render()
with tab6:
    tab6_wordcard.render()

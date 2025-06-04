import streamlit as st
import streamlit.components.v1 as components

from backend.explanation import get_explanation
from backend.favorite import is_favorited, toggle_favorite
from backend.vocab_status import get_vocab_status, set_vocab_status


def show_status(word: str, prefix: str) -> None:
    status = get_vocab_status(word)
    word_status_key: str = f"{prefix}_vocab_status_card_{word}"
    st.session_state.setdefault(
        word_status_key, status
    )  # セッションに初期値がなければ設定
    print(f"status = {status}")

    # UI 表示
    new_status = st.selectbox(
        "📘 単語の習得状態を選択",
        ["unknown", "passive", "active"],
        key=word_status_key,
        help="この単語の習得状態を選択してください。",
    )
    if new_status != status:
        print(f"new_status = {new_status}")
        set_vocab_status(word, new_status)
        st.success(f"「{word}」の語彙状態を「{new_status}」に更新しました！")


def show_favorite(word: str) -> None:
    """favorite button"""
    _, col2 = st.columns([4, 1])
    with col2:
        if is_favorited(word):
            if st.button("⭐", key=f"fav_remove_{word}", help="お気に入り解除"):
                toggle_favorite(word)
                st.rerun()
        else:
            if st.button("☆", key=f"fav_add_{word}", help="お気に入り追加"):
                toggle_favorite(word)
                st.rerun()


def speak_word_automatically(word: str) -> None:
    """ページ表示時に自動的に音声読み上げを行う"""
    components.html(
        f"""
        <script>
            const utterance = new SpeechSynthesisUtterance("{word}");
            utterance.lang = "en-US";
            speechSynthesis.cancel();
            speechSynthesis.speak(utterance);
        </script>
        """,
        height=0,
    )  # 高さ0でコンポーネントとしては見せない


def render_speak_button(word: str) -> None:
    """クリックで音声読み上げボタンを表示"""
    components.html(
        f"""
        <button onclick="const u = new SpeechSynthesisUtterance('{word}'); u.lang='en-US'; speechSynthesis.speak(u);">
            🔊 発音を聞く
        </button>
        """,
        height=50,
    )


def render_explanation(word_id: int) -> None:
    """単語の説明をMarkdownで表示"""
    with st.expander("詳細を見る"):
        explanation_md = get_explanation(word_id)
        if explanation_md:
            st.markdown(explanation_md, unsafe_allow_html=True)

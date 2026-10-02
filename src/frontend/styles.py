"""アイコンフォントの読み込みに依存しない展開矢印。"""

import streamlit as st

EXPANDER_ARROW_CSS = """
<style>
/* 展開ヘッダーだけを対象とし、本文や他のウィジェットには適用しない。 */
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    font-size: 0 !important;
    width: 1.25rem;
    min-width: 1.25rem;
    height: 1.25rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}
[data-testid="stExpander"] summary [data-testid="stIconMaterial"]::after {
    content: "";
    width: 0.4rem;
    height: 0.4rem;
    border-right: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: rotate(-45deg);
}
[data-testid="stExpander"] details[open] > summary [data-testid="stIconMaterial"]::after {
    transform: rotate(45deg);
}
</style>
"""


def apply_styles() -> None:
    st.markdown(EXPANDER_ARROW_CSS, unsafe_allow_html=True)

"""瞬間英作文: 回答を保存してから解答例を表示し、履歴から再挑戦する。"""

import sqlite3
from uuid import uuid4

import streamlit as st

from backend.practice_history import (
    Attempt,
    get_self_evaluations,
    initialize_history,
    list_attempts,
    save_attempt,
    save_self_evaluation,
)
from backend.practice_materials import get_sentence_materials

PREFIX = "composition_"


def start_practice(material: dict[str, str], retry_of: str | None = None) -> None:
    st.session_state[PREFIX + "material"] = material
    st.session_state[PREFIX + "retry"] = retry_of
    st.session_state[PREFIX + "attempt_id"] = str(uuid4())
    st.session_state[PREFIX + "saved"] = False
    st.session_state[PREFIX + "answer"] = ""


def render_answer(user_id: str) -> None:
    material = st.session_state[PREFIX + "material"]
    st.subheader(material["prompt"])
    st.caption(f"練習ポイント：{material['focus']}")
    saved = st.session_state[PREFIX + "saved"]
    with st.form(PREFIX + "answer_form"):
        answer = st.text_area(
            "英語で答えてください", key=PREFIX + "answer", disabled=saved
        )
        submitted = st.form_submit_button("回答を保存", disabled=saved)
    if submitted:
        if not answer.strip():
            st.warning("英文を入力してください。")
            return
        save_attempt(
            Attempt(
                st.session_state[PREFIX + "attempt_id"],
                user_id,
                "sentence_composition",
                material,
                {"text": answer.strip()},
                st.session_state[PREFIX + "retry"],
            )
        )
        st.session_state[PREFIX + "saved"] = True
        st.rerun()
    if saved:
        st.success("回答を保存しました。")
        show_example(material)
        render_rating(user_id)


def show_example(material: dict[str, str]) -> None:
    st.write("解答例：", material["example"])
    st.write(material["explanation"])
    st.caption("解答例以外にも正しい表現があります。現在は自己評価で振り返ります。")


def render_rating(user_id: str) -> None:
    attempt_id = st.session_state[PREFIX + "attempt_id"]
    with st.form(PREFIX + "rating_form"):
        rating = st.radio(
            "自己評価",
            ["できた", "迷った", "できなかった"],
            key=PREFIX + "rating_" + attempt_id,
        )
        if st.form_submit_button("自己評価を保存"):
            save_self_evaluation(attempt_id, user_id, rating)
            st.success("自己評価を保存しました。")


def render_history(user_id: str) -> None:
    st.subheader("これまでの回答")
    page = int(
        st.number_input("履歴ページ", min_value=1, step=1, key=PREFIX + "history_page")
    )
    attempts = list_attempts(user_id, "sentence_composition", offset=(page - 1) * 20)
    if not attempts:
        st.info("このページには回答履歴がありません。")
    for attempt in attempts:
        with st.expander(
            f"{attempt.created_at[:19]} UTC · {attempt.material['prompt']}"
        ):
            st.write("あなたの回答：", attempt.response["text"])
            show_example(attempt.material)
            ratings = get_self_evaluations(attempt.attempt_id, user_id)
            if ratings:
                st.write("自己評価：", " → ".join(ratings))
            if attempt.retry_of:
                st.caption("履歴から再挑戦した回答です。前の回答も履歴に残っています。")
            st.button(
                "この問題に再挑戦",
                key=PREFIX + "retry_" + attempt.attempt_id,
                on_click=start_practice,
                args=(attempt.material, attempt.attempt_id),
            )


def render_content(user_id: str) -> None:
    initialize_history()
    materials = get_sentence_materials()
    if PREFIX + "material" not in st.session_state:
        start_practice(materials[0])
    selected = st.selectbox(
        "問題を選ぶ",
        range(len(materials)),
        format_func=lambda index: f"{index + 1}. {materials[index]['focus']}",
        key=PREFIX + "selection",
    )
    st.button(
        "選んだ問題を始める",
        on_click=start_practice,
        args=(materials[selected],),
        key=PREFIX + "start",
    )
    render_answer(user_id)
    render_history(user_id)


def render(user_id: str = "default_user") -> None:
    st.header("✍️ 瞬間英作文")
    st.caption("回答を保存して振り返りましょう。再挑戦の回答は別の履歴として残ります。")
    try:
        render_content(user_id)
    except (sqlite3.Error, ValueError):
        st.error(
            "履歴の読み書きに失敗しました。入力内容は画面に保持しています。DBの設定を確認して再度お試しください。"
        )

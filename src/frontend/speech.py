"""ブラウザの英語音声を明示的に選ぶ読み上げ部品。"""

import json
from pathlib import Path

import streamlit.components.v1 as components


def render_speech(word: str, autoplay: bool = False) -> None:
    payload = json.dumps(
        {"word": word, "autoplay": autoplay}, ensure_ascii=True
    ).replace("<", "\\u003c")
    script = Path(__file__).with_name("speech.js").read_text(encoding="utf-8")
    components.html(
        '<label for="voice">読み上げ音声 </label>'
        '<select id="voice" aria-label="英語の読み上げ音声" style="max-width:100%" disabled></select>'
        '<p><button id="speak" disabled>🔊 発音を聞く・試聴</button></p>'
        + (
            '<label><input id="automatic" type="checkbox"> カードの自動読み上げ</label><br>'
            if autoplay
            else '<input id="automatic" type="checkbox" hidden>'
        )
        + '<small id="status" role="status"></small>'
        + f"<script>const speechConfig = {payload};\n{script}</script>",
        height=150,
    )

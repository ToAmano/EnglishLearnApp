"""音声選択をJSエンジンで検証する（pip install quickjs）。"""

import json
from pathlib import Path

import pytest

quickjs = pytest.importorskip("quickjs")
SCRIPT = Path(__file__).resolve().parents[2] / "src/frontend/speech.js"


def test_explicit_english_voice_and_saved_selection() -> None:
    context = quickjs.Context()
    context.eval(
        """
        const voices = [
          {voiceURI: "ja", name: "Japanese", lang: "ja-JP"},
          {voiceURI: "us", name: "English US", lang: "en-US"},
          {voiceURI: "gb", name: "English UK", lang: "en-GB"}
        ];
        const elements = {};
        const document = {getElementById: id => elements[id] ||= {
          value: "", textContent: "", disabled: false, options: [],
          replaceChildren() {this.options = []},
          append(option) {this.options.push(option); if (!this.value) this.value = option.value},
          addEventListener(type, fn) {this[type] = fn}
        }, createElement: () => ({})};
        const sessionStorage = {getItem: () => "gb", setItem: () => {}};
        let spoken;
        const speechSynthesis = {
          getVoices: () => voices, addEventListener() {}, cancel() {},
          speak(u) {spoken = u}
        };
        const window = {speechSynthesis};
        function SpeechSynthesisUtterance(text) {this.text = text}
        const speechConfig = {word: "hello", autoplay: false, scope: "card"};
    """
    )
    context.eval(SCRIPT.read_text())
    context.eval('elements["speak"].click()')
    assert json.loads(
        context.eval(
            "JSON.stringify([spoken.text, spoken.voice.voiceURI, spoken.lang])"
        )
    ) == ["hello", "gb", "en-GB"]
    assert context.eval('elements["voice"].options.length') == 2
    context.eval("voices.length = 0; populateVoices();")
    assert context.eval('elements["speak"].disabled')

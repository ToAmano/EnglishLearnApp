const synth = window.speechSynthesis;
const selector = document.getElementById("voice");
const button = document.getElementById("speak");
const status = document.getElementById("status");
const storageKey = "englishapp.speech.voice";
let englishVoices = [];
function readPreference(key) {
    try { return sessionStorage.getItem(key); } catch (_) { return null; }
}
function savePreference(key, value) {
    try { sessionStorage.setItem(key, value); } catch (_) { /* 保存不可でも再生する */ }
}
function populateVoices() {
    if (!synth) { status.textContent = "このブラウザは読み上げに対応していません。"; return; }
    englishVoices = synth.getVoices().filter(v => /^en(?:-|_)/i.test(v.lang));
    englishVoices.sort((a, b) => Number(b.lang === "en-US") - Number(a.lang === "en-US"));
    const preferred = readPreference(storageKey) || selector.value;
    selector.replaceChildren();
    for (const voice of englishVoices) {
        const option = document.createElement("option");
        option.value = voice.voiceURI;
        option.textContent = `${voice.name} (${voice.lang})`;
        selector.append(option);
    }
    if (englishVoices.some(v => v.voiceURI === preferred)) selector.value = preferred;
    selector.disabled = button.disabled = englishVoices.length === 0;
    status.textContent = englishVoices.length ? "声を選び、発音を聞いて比較できます。" : "英語音声を読み込み中です。端末の英語音声設定も確認してください。";
}
function speak() {
    const voice = englishVoices.find(v => v.voiceURI === selector.value);
    if (!voice) return;
    const utterance = new SpeechSynthesisUtterance(speechConfig.word);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onerror = event => {
        if (!["canceled", "interrupted"].includes(event.error)) {
            status.textContent = "再生できませんでした。別の声を選んで発音ボタンを押してください。";
        }
    };
    synth.cancel();
    synth.speak(utterance);
}
selector.addEventListener("change", () => savePreference(storageKey, selector.value));
button.addEventListener("click", speak);
populateVoices();
if (synth) synth.addEventListener("voiceschanged", populateVoices);
const automatic = document.getElementById("automatic");
const automaticKey = "englishapp.speech.automatic";
automatic.checked = readPreference(automaticKey) === "true";
automatic.addEventListener("change", () => {
    savePreference(automaticKey, String(automatic.checked));
    if (automatic.checked) speak();
});
function playNewCard() {
    if (!speechConfig.autoplay || !automatic.checked || !englishVoices.length) return;
    const lastKey = "englishapp.speech.lastCard";
    if (readPreference(lastKey) === speechConfig.word) return;
    savePreference(lastKey, speechConfig.word);
    speak();
}
if (speechConfig.autoplay) {
    if (synth) synth.addEventListener("voiceschanged", playNewCard);
    playNewCard();
}

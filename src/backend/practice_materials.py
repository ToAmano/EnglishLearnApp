"""最初の短文教材。出題時の内容は回答履歴にも保存する。"""


def get_sentence_materials() -> list[dict[str, str]]:
    examples = [
        (
            "私は毎朝コーヒーを飲みます。",
            "I drink coffee every morning.",
            "現在形",
            "習慣は現在形で表します。",
        ),
        (
            "彼女は今、夕食を作っています。",
            "She is cooking dinner now.",
            "現在進行形",
            "今していることは be + 動詞のing形で表します。",
        ),
        (
            "あなたは昨日、図書館に行きましたか。",
            "Did you go to the library yesterday?",
            "過去の疑問文",
            "Did の後は動詞の原形です。",
        ),
        (
            "私は3年前からここに住んでいます。",
            "I have lived here for three years.",
            "現在完了",
            "期間には for を使います。I have been living here for three years. も自然です。",
        ),
        (
            "この本はあの本より面白いです。",
            "This book is more interesting than that one.",
            "比較級",
            "比較する相手は than で示します。",
        ),
        (
            "私は泳ぐことができます。",
            "I can swim.",
            "助動詞",
            "can の後は動詞の原形です。",
        ),
        (
            "私は明日早く起きなければなりません。",
            "I have to get up early tomorrow.",
            "義務",
            "I must get up early tomorrow. も可能です。",
        ),
        (
            "窓を開けていただけますか。",
            "Could you open the window?",
            "依頼",
            "Would you open the window? などの別解もあります。",
        ),
        (
            "もし明日雨が降ったら、私は家にいます。",
            "If it rains tomorrow, I will stay home.",
            "条件文",
            "未来の条件でも if 節では現在形を使います。",
        ),
        (
            "私は英語を勉強するためにこの本を買いました。",
            "I bought this book to study English.",
            "不定詞",
            "目的を to + 動詞の原形で表します。",
        ),
    ]
    return [
        {
            "id": f"sentence-{index:03d}",
            "version": "1",
            "prompt": prompt,
            "example": example,
            "focus": focus,
            "explanation": explanation,
        }
        for index, (prompt, example, focus, explanation) in enumerate(examples, start=1)
    ]

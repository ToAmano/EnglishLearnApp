import os
import time
from logging import DEBUG, INFO, StreamHandler, getLogger
from typing import List

import pandas as pd
from dotenv import load_dotenv
from IPython.display import Markdown, display
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAI
from pydantic import BaseModel, Field

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)

# 環境変数からAPIキーを読み込む
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NUMBER_OF_EXAMPLES = os.getenv("NUMBER_OF_EXAMPLES", default=5)


from langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # <-- Super slow! We can only make a request once every 10 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

# Gemini APIの初期化
llm = GoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY, rate_limiter=rate_limiter
)


# 例文生成用のプロンプトテンプレート
example_prompt = PromptTemplate.from_template(
    """Generate the detailed dictionary-like explanation of the English word "{word}" for Japanese learners in markdown format.
    
    Requirements:
    - provide detailed meaning and nuance of the word in Japanese
    - If the word is a noum, provide the noun form (countable or uncountable) and its meaning
    - provide famous collocations and idioms
    - provide derivative words
    - explain the synonyms and antonyms with their proper usage 
    - follow the example format below
    - Do not include ```markdown at the beginning and end of the output
    
    example:
    # 📚 `abound` ― Detailed Explanation

    ## ✅ 単語の意味やニュアンス

    - **哲語**: 自動語 (intransitive verb)
    - **意味**:
    - (物、情報などが)豊富にある
    - (場所が)「−で満ちている」

    ### 🔹 ニュアンス

    - 抽象的、自然な存在を記述する際に使用
    - 人間は主語にならない
    - ややフォーマルな文体

    #### 例文

    ```markdown
    - The forest abounds with wildlife.
    - Rumors abound about the celebrity's sudden disappearance.
    - Opportunities abound for those who are willing to seek them.
    ```

    ---

    ## 🌱 語源

    - ラテン語 **"abundare"** = 溢れる、満ちる
    - **ab-** (離れて) + **unda** (波) → 波が溢れるように満ちる

    ---

    ## 🔗 頻出のコロケーション

    | コロケーション | 意味・用途 |
    |----------------|----------------|
    | **abound in** + 名詞 | ～に富む (資源、成分) |
    | **abound with** + 名詞 | ～で満ちている (動物、情報) |
    | **rumors abound** | うわさが湧いている |
    | **opportunities abound** | チャンスが豊富にある |
    | **wildlife abounds** | 自然、動物が多く存在する |

    ---

    ## 🔄 源語語

    | 単語 | 哲語 | 意味 | 用例 |
    |--------|--------|--------|--------|
    | **abundant** | 形容語 | 豊富な | *an abundant supply of water* |
    | **abundance** | 名詞 | 豊富 | *live in abundance* |
    | **abundantly** | 副語 | 豊かに | *abundantly clear* (非常に明白) |

    ---

    ## 🔄 類語・対義語（使い分け含む）

    ### 類語 (synonyms)

    | 単語 | ニュアンス | 例文 |
    |--------|-------------|-------|
    | **be plentiful** | 数が多い、ややカジュアル | *Resources were plentiful in the area.* |
    | **overflow with** | 物理的に溢れている | *Her inbox overflowed with messages.* |
    | **teem with** | 人や動物がうごめいている | *The market teems with people.* |
    | **be rich in** | 特定の成分に富む | *The soil is rich in nutrients.* |
    | **proliferate** | 急増する（抽象） | *Fake news has proliferated online.* |

    ### 対義語 (antonyms)

    | 単語 | ニュアンス | 例文 |
    |--------|-------------|--------|
    | **lack** | ～がない | *He lacks motivation.* |
    | **be scarce** | 少ない、得がたい | *Food was scarce during the war.* |
    | **be short of** | ～が足りない | *We're short of time.* |
    | **be devoid of** | 完全に缺けている | *His speech was devoid of passion.* |

    ---

    ## 📀 まとめ

    | 項目 | 内容 |
    |------|------|
    | 品詞 | 自動詞 |
    | 意味 | 豊富にある、～で満ちている |
    | 語源 | ラテン語 "abundare"（あふれ出る） |
    | よく使う形 | abound in / abound with |
    | 派生語 | abundant, abundance, abundantly |
    | 類語 | be plentiful, teem with, overflow with, be rich in, proliferate |
    | 対義語 | lack, be scarce, be short of, be devoid of |
    | 使用場面 | 自然、情報、機会などが豊富な状況の描写に最適。フォーマルな文で多用される |

    """
)

# Chain
chain = example_prompt | llm | StrOutputParser()


def load_input_csv(input_file: str):
    # 入力CSVの読み込み(重複なしの想定)
    try:
        df = pd.read_csv(
            input_file, dtype={"word_id": int, "word": str}, na_filter=False
        )
    except Exception as e:
        print(f"CSVファイルの読み込みエラー: {e}")
        raise ValueError(f"CSVファイルの読み込みエラー: {e}")
    return df


def check_existing_words(output_file: str):
    """既存の出力ファイルをチェックし、完全に処理された単語を取得する"""

    fully_processed_words = set()
    word_explanation_dict = {}

    if not os.path.exists(output_file):
        return fully_processed_words, word_explanation_dict

    try:
        existing_df = pd.read_csv(
            output_file,
            dtype={"word_id": int, "word": str, "explanation": str},
            na_filter=False,
        )
        # NaNの処理を改善（pandasの標準的な方法でNaNをチェック）
        for index, row in existing_df.iterrows():
            word = row["word"]
            explanation = row["explanation"]
            if pd.notna(explanation) and explanation != "":
                fully_processed_words.add(word)
                word_explanation_dict[word] = explanation
        print(
            f"既存の出力ファイルから{len(fully_processed_words)}件のデータを読み込みました。"
        )
    except Exception as e:
        print(f"既存の出力ファイルの読み込みエラー: {e}")
    return fully_processed_words, word_explanation_dict


def generate_example(word: str) -> List[str]:
    """単語に対して例文を生成する"""
    # 例文の生成
    output = chain.invoke({"word": word})
    # 出力をパース
    examples: str = output  # .explanation
    return examples


def convert_to_long_format(results: List[dict], word_id_dict: dict) -> List[dict]:
    """結果をロング形式に変換する"""
    long_format_results = []
    for index, row in word_id_dict.iterrows():
        word = row["word"]
        word_id = row["word_id"]

        if word in results:
            long_format_results.append(
                {
                    "word_id": word_id,
                    "word": word,
                    "explanation": results[word],
                }
            )
    return long_format_results


def process_csv(input_file, output_file):
    """入力CSVファイルを処理し、各単語に例文を追加して新しいCSVに保存する"""
    df = load_input_csv(input_file)

    # 既存の出力ファイルをチェック（続きから処理するため）
    fully_processed_words, word_explanation_dict = check_existing_words(output_file)

    # 各単語を処理
    for index, row in df.iterrows():
        word = row["word"]

        # 既に処理済みの単語はスキップ
        if word in fully_processed_words:
            print(f"スキップ: {word} (既に処理済み)")
            continue
        print(f"処理中: {word} ({index+1}/{len(df)})")

        try:
            # 例文を生成
            examples = generate_example(word)
            # 結果を辞書に追加または更新
            word_explanation_dict[word] = examples
        except Exception as e:
            print(f"単語「{word}」の処理中にエラーが発生: {e}")
            # エラーが発生した場合も、空の例文で結果を追加して保存
            word_explanation_dict[word] = ""

        # 形式を変形し，ファイルに保存
        long_format_results = convert_to_long_format(word_explanation_dict, df)
        pd.DataFrame(long_format_results).to_csv(
            output_file, index=False, encoding="utf-8"
        )
        print(f"  → {word}の処理完了。中間結果を保存しました。")
        # APIリクエスト制限を考慮して少し待機
        time.sleep(5)

    print(f"処理が完了しました。結果は {output_file} に保存されています。")


# 使用例
if __name__ == "__main__":
    # input_file = "../generate_examples/lv6.csv"  # 入力ファイル名
    input_file = "../word_data/eiken_derujun_added.csv"
    output_file = "eiken_derujun_detail.csv"  # 出力ファイル名

    process_csv(input_file, output_file)

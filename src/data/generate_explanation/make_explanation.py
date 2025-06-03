import os
import time
from logging import DEBUG, StreamHandler, getLogger
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import GoogleGenerativeAI

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)

# 環境変数からAPIキーを読み込む
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NUMBER_OF_EXAMPLES = int(os.getenv("NUMBER_OF_EXAMPLES", default="5"))


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
    # 📚 `comprise` ― Detailed Explanation

    ## ✅ 単語の意味やニュアンス

    - **品詞**: 他動詞 (transitive verb)
    - **意味**:
        - (全体が部分を)含む、構成する
        - (部分が全体を)構成する (ややフォーマル)

    ### 🔹 ニュアンス

    - 全体と部分の関係を表す言葉です。
    - `comprise`は、全体が部分を「含む」という意味でよく使われます。
    - フォーマルな文体で使われることが多いです。
    - 受動態で使うことは避けるべきです (後述)。

    #### 例文

    - The committee comprises ten members. (委員会は10人のメンバーで構成されている。)
    - The United Kingdom comprises England, Scotland, Wales, and Northern Ireland. (イギリスは、イングランド、スコットランド、ウェールズ、北アイルランドから構成されている。)
    - The book comprises six chapters. (その本は6つの章から構成されている。)


    ---

    ## 🌱 語源

    - フランス語 **""comprendre""** = 理解する、含む
    - ラテン語 **""comprehendere""** = 把握する、包含する
    - **com-** (共に) + **prehendere** (掴む) → 全てを掴む、包含する

    ---

    ## 🔗 頻出のコロケーション

    | コロケーション | 意味・用途 |
    |----------------|----------------|
    | **comprise of** + 名詞 | (非推奨) ～から構成される  (誤用とみなされることが多い) |
    | **comprise ... members** | ～人のメンバーから構成される |
    | **comprise ... chapters** | ～章から構成される |
    | **comprise ... elements** | ～の要素から構成される |

    **注意点**:
    * `comprise of` は誤用とみなされることが多く、`consist of` や `be composed of` を使うのがより適切です。

    ---

    ## 🔄 派生語

    | 単語 | 品詞 | 意味 | 用例 |
    |--------|--------|--------|--------|
    | **composition** | 名詞 | 構成、組成、作文 | *The composition of the committee.* |
    | **composite** | 形容詞/名詞 | 合成の、複合の/複合材 | *a composite material* |

    ---

    ## 🔄 類語・対義語（使い分け含む）

    ### 類語 (synonyms)

    | 単語 | ニュアンス | 例文 |
    |--------|-------------|-------|
    | **consist of** | ～から成る (部分が全体を構成する) | *The team consists of five players.* |
    | **be composed of** | ～から構成される (部分が全体を構成する) | *The cake is composed of flour, sugar, and eggs.* |
    | **include** | ～を含む (全体の一部を含む) | *The price includes breakfast.* |
    | **contain** | ～を含む (物理的に含む) | *The box contains books.* |
    | **be made up of** | ～から構成されている (口語的) | *The group is made up of volunteers.* |

    **使い分け**:

    * `comprise`: 全体 = 部分 + 部分 + 部分... (全体が部分を包含する、または部分が全体を構成する)
    * `consist of`: 全体 = 部分 + 部分 + 部分... (部分が全体を構成する)
    * `be composed of`: `consist of` とほぼ同じ意味で、よりフォーマル。
    * `include`: 全体 ⊃ 部分 (全体が部分を含む。全てを列挙するわけではない)
    * `contain`: 物理的に含む場合や、抽象的な要素を含む場合にも使える。
    * `be made up of`: 口語的で、`consist of` と同様の意味。

    ### 対義語 (antonyms)

    | 単語 | ニュアンス | 例文 |
    |--------|-------------|--------|
    | **exclude** | ～を除外する | *The price excludes tax.* |
    | **omit** | ～を省略する | *He omitted the details.* |
    | **lack** | ～を欠く | *The essay lacks clarity.* |

    ---

    ## 📀 まとめ

    | 項目 | 内容 |
    |------|------|
    | 品詞 | 他動詞 |
    | 意味 | (全体が部分を)含む、構成する、(部分が全体を)構成する |
    | 語源 | フランス語 ""comprendre"" (理解する、含む) |
    | よく使う形 | The whole comprises the parts. The parts comprise the whole. |
    | 派生語 | composition, composite |
    | 類語 | consist of, be composed of, include, contain, be made up of |
    | 対義語 | exclude, omit, lack |
    | 使用場面 | 全体と部分の関係を説明する際に使用。フォーマルな文で多用される。 |
    """
)

# Chain
chain = example_prompt | llm | StrOutputParser()


def check_existing_words(check_file: str) -> Tuple[Set[str], Dict[str, str]]:
    """既存の出力ファイルをチェックし、完全に処理された単語を取得する"""

    fully_processed_words: Set[str] = set()
    word_explanation_dict: Dict[str, str] = {}

    if not os.path.exists(check_file):
        return fully_processed_words, word_explanation_dict

    try:
        existing_df = pd.read_csv(
            check_file,
            dtype={"word_id": int, "word": str, "explanation": str},
            na_filter=False,
        )
        # NaNの処理を改善（pandasの標準的な方法でNaNをチェック）
        for _, row in existing_df.iterrows():
            word = row["word"]
            explanation = row["explanation"]
            if pd.notna(explanation) and explanation != "":
                fully_processed_words.add(word)
                word_explanation_dict[word] = explanation
        print(
            f"既存の出力ファイルから{len(fully_processed_words)}件のデータを読み込みました。"
        )
    except Exception as e:
        raise e
    return fully_processed_words, word_explanation_dict


def generate_explanation(word: str) -> str:
    """Generate detailed explanation from LLM for given word"""
    output: str = chain.invoke({"word": word})
    return output


def convert_to_long_format(
    results: Dict[Any, Any], word_id_dict: pd.DataFrame
) -> List[Dict[Any, Any]]:
    """結果をロング形式に変換する"""
    long_format_results = []
    for _, row in word_id_dict.iterrows():
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


def process_csv(input_file: str, output_file: str) -> None:
    """入力CSVファイルを処理し、各単語に例文を追加して新しいCSVに保存する"""
    df: pd.DataFrame = pd.read_csv(
        input_file, dtype={"word_id": int, "word": str}, na_filter=False
    )

    # 既存の出力ファイルをチェック（続きから処理するため）
    fully_processed_words, word_explanation_dict = check_existing_words(output_file)

    # 各単語を処理
    for index, row in df.iterrows():
        word = row["word"]

        # 既に処理済みの単語はスキップ
        if word in fully_processed_words:
            print(f"スキップ: {word} (既に処理済み)")
            continue
        print(f"処理中: {word} ( {index + 1} / {len(df)} )")

        try:
            # 例文を生成
            generated_explanation = generate_explanation(word)
            # 結果を辞書に追加または更新
            word_explanation_dict[word] = generated_explanation
        except Exception as e:  # pylint: disable=broad-exception-caught
            # エラーが発生した場合も、空の例文で結果を追加して保存
            word_explanation_dict[word] = ""
            print(f"単語「{word}」の処理中にエラーが発生: {e}")

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
    input_filename: str = "../word_data/eiken_derujun_added.csv"
    output_filename: str = "eiken_derujun_detail.csv"  # 出力ファイル名

    process_csv(input_filename, output_filename)

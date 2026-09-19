import csv
import json
import os
import time
from logging import DEBUG, INFO, StreamHandler, getLogger
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import typer
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.rate_limiters import InMemoryRateLimiter
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


# 構造化出力のためのPydanticモデル
class ExampleSentences(BaseModel):
    synonyms: List[str] = Field(
        ..., description="List of synonym words for the given word"
    )


rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # <-- Super slow! We can only make a request once every 10 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

# Gemini APIの初期化
llm = GoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY, rate_limiter=rate_limiter
)

output_parser = PydanticOutputParser(pydantic_object=ExampleSentences)

# format_instructions を生成
format_instructions = output_parser.get_format_instructions()


# 例文生成用のプロンプトテンプレート
example_prompt = PromptTemplate.from_template(
    """Provide synonyms as much as possible for the English word "{word}".

    Requirements:
    - Include both basic (easy) and advanced (difficult) synonyms.
    - Include both single words and short phrases if appropriate.
    - Cover both direct synonyms and related words used in similar contexts.

    {format_instructions}
    """
)
# format_instructionsをテンプレートに挿入
example_prompt = example_prompt.partial(format_instructions=format_instructions)

# Chain
chain = example_prompt | llm | output_parser


def load_input_csv(input_file: str):
    # 入力CSVの読み込み(重複なしの想定)
    try:
        df = pd.read_csv(
            input_file, dtype={"number": int, "word": str}, na_filter=False
        )
    except Exception as e:
        print(f"CSVファイルの読み込みエラー: {e}")
        raise ValueError(f"CSVファイルの読み込みエラー: {e}")
    return df


def check_existing_words(output_file: str):
    """既存の出力ファイルをチェックし、完全に処理された単語を取得する"""

    fully_processed_words = set()
    word_example_dict = {}

    if not os.path.exists(output_file):
        return fully_processed_words, word_example_dict

    try:
        existing_df = pd.read_csv(
            output_file,
            dtype={"number": int, "word": str, "synonym": str},
            na_filter=False,
        )
        # NaNの処理を改善（pandasの標準的な方法でNaNをチェック）
        for word, group in existing_df.groupby("word"):
            examples = group["synonym"].tolist()
            # NaNでない例文が存在するかチェック
            valid_examples = [ex for ex in examples if pd.notna(ex) and ex != ""]

            if valid_examples:
                logger.debug(f"単語: {word}, synonym: {valid_examples}")
                fully_processed_words.add(word)
                word_example_dict[word] = valid_examples
        logger.info(
            f"既存の出力ファイルから{len(fully_processed_words)}件のデータを読み込みました。"
        )
    except Exception as e:
        logger.error(f"既存の出力ファイルの読み込みエラー: {e}")
    return fully_processed_words, word_example_dict


def generate_example(word: str) -> List[str]:
    """単語に対して例文を生成する"""
    # 例文の生成
    output = chain.invoke({"word": word})
    # 出力をパース
    synonyms: List[str] = output.synonyms
    return synonyms


def convert_to_long_format(results: dict, word_id_df: pd.DataFrame) -> List[dict]:
    """結果をロング形式に変換する"""
    long_format_results = []
    for index, row in word_id_df.iterrows():
        word = row["word"]
        word_id = row["number"]

        if word in results:
            for synonym in results[word]:
                long_format_results.append(
                    {"number": word_id, "word": word, "synonym": synonym}
                )
        else:  # 処理できなかった単語も追加 (synonymは空)
            long_format_results.append({"number": word_id, "word": word, "synonym": ""})
    return long_format_results


def process_csv(input_file: Path, output_file: Path):
    """入力CSVファイルを処理し、各単語に例文を追加して新しいCSVに保存する"""
    df = load_input_csv(str(input_file))

    # 既存の出力ファイルをチェック（続きから処理するため）
    fully_processed_words, word_example_dict = check_existing_words(str(output_file))

    # 各単語を処理
    for index, row in df.iterrows():
        word_id: int = row["number"]
        word = row["word"]

        # 既に処理済みの単語はスキップ
        if word in fully_processed_words:
            logger.info(f"スキップ: {word} (既に処理済み)")
            continue
        logger.info(f"処理中: {word} ({index+1}/{len(df)})")

        try:
            # 例文を生成
            examples = generate_example(word)
            # 結果を辞書に追加または更新
            word_example_dict[word] = examples
        except Exception as e:
            logger.error(f"単語「{word}」の処理中にエラーが発生: {e}")
            # エラーが発生した場合も、空の例文で結果を追加して保存
            word_example_dict[word] = [""]

        # 形式を変形し，ファイルに保存
        long_format_results = convert_to_long_format(word_example_dict, df)
        pd.DataFrame(long_format_results).to_csv(
            output_file, index=False, encoding="utf-8"
        )
        logger.info(f"  → {word}の処理完了。中間結果を保存しました。")
        # APIリクエスト制限を考慮して少し待機
        time.sleep(5)

    logger.info(f"処理が完了しました。結果は {output_file} に保存されています。")


app_synonym = typer.Typer()


@app_synonym.command()
def generate_synonyms(
    input_file: Path = typer.Option(
        ..., "--input-file", "-i", help="入力CSVファイルのパス。"
    ),
    output_file: Path = typer.Option(
        ..., "--output-file", "-o", help="出力CSVファイルのパス。"
    ),
):
    """
    入力CSVファイルから単語を読み込み、それぞれの単語の類義語を生成してCSVファイルに保存します。
    """
    process_csv(input_file, output_file)

"""Gemini APIを使用して画像を生成するスクリプト。

このスクリプトは、LangChainとGoogle Generative AI APIを利用して、
指定されたプロンプトに基づいた画像を生成し、ローカルに保存します。

主な機能:
- 指定されたテキストプロンプトから画像を生成します。
- 生成された画像をbase64からデコードし、ファイルとして保存します。
- 設定可能なパラメータ（生成枚数、出力ディレクトリなど）に対応します。
- 非同期処理による効率的な画像生成が可能です。
"""

import asyncio
import base64
import datetime
import os
from io import BytesIO
from typing import Any, Dict, List

import nest_asyncio
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI, Modality
from PIL import Image

nest_asyncio.apply()


def get_api_key() -> str:
    """環境変数からGoogle APIキーを取得します。

    .envファイルからAPIキーを読み込みます。
    キーが存在しない場合はValueErrorを送出します。

    Returns:
        str: Google APIキー。

    Raises:
        ValueError: APIキーが環境変数に設定されていない場合。
    """
    _ = load_dotenv(find_dotenv())
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEYが環境変数に設定されていません。")
    return api_key


def base64_to_image(base64_str: str) -> Image.Image:
    """base64文字列をPillowのImageオブジェクトに変換します。

    Args:
        base64_str (str): 画像のbase64エンコード文字列。

    Returns:
        Image.Image: PillowのImageオブジェクト。
    """
    img_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(img_data))


def save_image(
    image: Image.Image, output_dir: str = "outputs/new_generation"
) -> str:
    """画像をファイルとして保存します。

    ファイル名はタイムスタンプを元に一意に生成されます。

    Args:
        image (Image.Image): 保存するPillowのImageオブジェクト。
        output_dir (str, optional): 画像の保存先ディレクトリ。
                                    デフォルトは "outputs/new_generation"。

    Returns:
        str: 保存された画像のファイルパス。

    Raises:
        IOError: ファイルの保存に失敗した場合。
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{output_dir}/generate_{timestamp}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        image.save(filename)
        print(f"画像を保存しました: {filename}")
        return filename
    except IOError as e:
        print(f"エラー: 画像の保存に失敗しました - {e}")
        raise


def process_generation_results(contents: List[Dict[str, str]], output_dir: str):
    """LLMの生成結果を処理し、画像を保存、テキストを表示します。

    Args:
        contents (List[Dict[str, str]]):
            LLMの出力結果のリスト。テキストは'str'キー、
            画像は'base64'キーを持つ辞書で構成されます。
        output_dir (str): 画像の保存先ディレクトリ。
    """
    print("=" * 12, " 生成結果 ", "=" * 12)
    for res in contents:
        if "base64" in res:
            image = base64_to_image(res["base64"])
            save_image(image, output_dir)
        elif "str" in res:
            print(f"出力テキスト: {res['str']}")
    print("=" * 38)


def extract_content_from_response(response: Any) -> List[Dict[str, str]]:
    """LLMのレスポンスからテキストとbase64画像を抽出します。

    Args:
        response (Any): LLMからの生のレスポンスオブジェクト。

    Returns:
        List[Dict[str, str]]: 抽出されたコンテンツのリスト。
                               例: [{'str': 'テキスト'}, {'base64': '...'}]

    Raises:
        ValueError: レスポンスの形式が不正な場合。
    """
    if not hasattr(response, "content"):
        raise ValueError("レスポンスに'content'属性が存在しません。")

    content = response.content
    if not isinstance(content, list) or not content:
        print(f'生成結果: "{content}"')
        raise ValueError("レスポンスの'content'が空またはリスト形式ではありません。")

    extracted_list = []
    for i, item in enumerate(content):
        if isinstance(item, str):
            extracted_list.append({"str": item})
        elif isinstance(item, dict):
            image_url = item.get("image_url")
            if not isinstance(image_url, dict) or "url" not in image_url:
                raise ValueError(f"content[{i}]の'image_url'の形式が不正です。")

            url = image_url["url"]
            if not isinstance(url, str) or "," not in url:
                raise ValueError(f"content[{i}]の'url'の形式が不正です。")

            base64_str = url.split(",")[-1]
            extracted_list.append({"base64": base64_str})
        else:
            raise ValueError(f"content[{i}]は想定外の型です: {type(item)}")

    return extracted_list


def create_generation_chain(api_key: str) -> Runnable:
    """画像生成用のLangChainチェーンを作成します。

    Args:
        api_key (str): Google APIキー。

    Returns:
        Runnable: 画像生成を実行するためのLangChainチェーン。
    """
    model = ChatGoogleGenerativeAI(
        model="models/gemini-2.0-flash-exp-image-generation",
        google_api_key=api_key,
        response_modalities=[Modality.IMAGE, Modality.TEXT],
    )

    # Gemini 2.0 Flash Image Generationは現在SystemMessageをサポートしていません。
    # そのため、HumanMessageでタスクの指示を与えます。
    prompt_messages = [
        HumanMessage(
            content="""# 目的
あなたのタスクは画像生成です。ユーザが指定した内容で新しい画像を生成してください。

----以下がユーザの入力です----
"""
        ),
        HumanMessagePromptTemplate.from_template(
            [{"type": "text", "text": "{user_input}"}]
        ),
    ]

    prompt = ChatPromptTemplate.from_messages(prompt_messages)
    return prompt | model


async def generate_image_async(
    chain: Runnable, query: str, generation_number: int
) -> List[Dict[str, str]]:
    """非同期で単一の画像を生成し、結果を抽出します。

    Args:
        chain (Runnable): LangChainの実行可能チェーン。
        query (str): 画像生成のためのテキストプロンプト。
        generation_number (int): 現在の生成回数（ログ出力用）。

    Returns:
        List[Dict[str, str]]: 抽出されたコンテンツのリスト。
    """
    print(f"画像{generation_number}の生成を開始します。")
    try:
        response = await chain.ainvoke(
            {"user_input": query},
            generation_config=dict(response_modalities=["TEXT", "IMAGE"]),
        )
        return extract_content_from_response(response)
    except ValueError as e:
        print(f"画像{generation_number}の生成中にエラーが発生しました: {e}")
        return []
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return []


async def main():
    """スクリプトのメインエントリポイント。

    画像生成の設定を行い、非同期で画像を生成・保存します。
    """
    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"エラー: {e}")
        return

    # --- 設定 ---
    num_generations = 5  # 生成する画像の枚数 (RPM 10を考慮)
    output_directory = "outputs/new_generation"
    query = (
        "家のPCデスクの実写画像を作成してください。"
        "机の上にはノートPCとコーヒーカップを置いてください。"
        "机の色は黒色でお願いします。"
        "そのほかは一般的な部屋の様子でいい感じに作ってください。"
    )
    # --- 設定ここまで ---

    chain = create_generation_chain(api_key)

    tasks = [
        generate_image_async(chain, query, i + 1) for i in range(num_generations)
    ]
    results = await asyncio.gather(*tasks)

    for extracted_content in results:
        if extracted_content:
            process_generation_results(extracted_content, output_directory)


if __name__ == "__main__":
    asyncio.run(main())
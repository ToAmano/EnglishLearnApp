import asyncio


async def generate_explanation_for_word(word: str) -> str:
    """
    指定された単語に対してLLMを呼び出し、説明文を生成する非同期関数。

    Args:
        word: 説明文を生成する単語。

    Returns:
        生成された説明文の文字列。

    Raises:
        Exception: LLM API呼び出し中にエラーが発生した場合。
    """
    # --- ここに実際のLLM API呼び出しロジックを実装します ---
    # 例:
    # client = httpx.AsyncClient()
    # response = await client.post(
    #     "https://api.example.com/generate",
    #     json={"word": word, "model": "gpt-4o"},
    #     headers={"Authorization": "Bearer YOUR_API_KEY"},
    #     timeout=30.0,
    # )
    # response.raise_for_status()
    # return response.json()["explanation"]
    # ----------------------------------------------------

    # 以下は、ネットワーク遅延をシミュレートするプレースホルダーです。
    # 0.5秒から1.5秒のランダムな遅延を発生させます。
    delay = 0.5 + asyncio.get_running_loop().time() % 1.0
    await asyncio.sleep(delay)

    # 10%の確率で意図的にエラーを発生させ、エラーハンドリングをテストします。
    if asyncio.get_running_loop().time() % 10 < 1:
        raise Exception("LLM API rate limit exceeded")

    return f"This is a generated explanation for the word '{word}'."

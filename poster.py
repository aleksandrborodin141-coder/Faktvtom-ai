import os
import asyncio
from openai import OpenAI

async def main():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY не найден. Проверь секрет в GitHub Actions."
        )

    client = OpenAI(api_key=api_key)

    print("OpenAI API key найден, продолжаю работу...")

    # твой дальнейший асинхронный код

if __name__ == "__main__":

    asyncio.run(main())

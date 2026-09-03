import os
import asyncio
from openai import OpenAI
from telegram import Bot

async def main():
    groq_key = os.getenv("GROQ_API_KEY")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("CHANNEL_USERNAME")

    if not groq_key:
        raise RuntimeError("GROQ_API_KEY не найден.")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не найден.")
    if not channel:
        raise RuntimeError("CHANNEL_USERNAME не найден.")

    print("Все секреты найдены.")

    client = OpenAI(
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "Ты автор Telegram-канала. Пиши короткие, интересные посты на русском языке."},
            {"role": "user", "content": "Напиши один интересный факт для канала. Длина — 2-4 предложения."}
        ],
        max_tokens=300,
        temperature=0.8
    )

    raw_text = response.choices[0].message.content
    print(f"Ответ от Groq: {repr(raw_text)}")

    if raw_text:
        text = raw_text.strip()
    else:
        text = "Интересный факт: каждый день — это новая возможность узнать что-то новое."

    print(f"Сгенерировано: {text[:80]}...")

    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=channel, text=text)
    print("Отправлено!")

if __name__ == "__main__":
    asyncio.run(main())

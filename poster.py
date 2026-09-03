import os
import asyncio
from openai import OpenAI
from telegram import Bot

async def main():
    # Получаем секреты из окружения
    openai_key = os.getenv("OPENAI_API_KEY")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("CHANNEL_USERNAME")

    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY не найден. Проверь секрет в GitHub Actions.")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не найден. Проверь секрет в GitHub Actions.")
    if not channel:
        raise RuntimeError("CHANNEL_USERNAME не найден. Проверь секрет в GitHub Actions.")

    print("Все секреты найдены, продолжаю работу...")

    # Генерация текста через OpenAI
    client = OpenAI(api_key=openai_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты автор Telegram-канала. Пиши короткие, интересные посты на русском языке."},
                {"role": "user", "content": "Напиши один интересный факт или мысль для канала. Длина — 2-4 предложения."}
            ],
            max_tokens=300,
            temperature=0.8
        )
        text = response.choices[0].message.content.strip()
        print(f"Сгенерирован текст: {text[:100]}...")
    except Exception as e:
        print(f"Ошибка OpenAI: {e}")
        raise

    # Отправка в Telegram
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=channel, text=text)
        print("Сообщение успешно отправлено в Telegram!")
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        raise

if name == "main":
    asyncio.run(main())

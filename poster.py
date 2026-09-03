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

    print("Все секреты найдены. Генерирую пост...")

    client = OpenAI(
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты автор популярного Telegram-канала. "
                    "Пишешь цепляющие посты на русском языке. "
                    "Каждый пост состоит из короткого заголовка (1 строка) "
                    "и развёрнутого текста (5-8 предложений). "
                    "Без эмодзи, без хештегов."
                )
            },
            {
                "role": "user",
                "content": (
                    "Напиши пост в строгом формате:\n"
                    "ЗАГОЛОВОК: <заголовок>\n"
                    "ТЕКСТ: <развёрнутый текст поста>\n\n"
                    "Тема: один интересный факт, мысль или наблюдение."
                )
            }
        ],
        max_tokens=600,
        temperature=0.8
    )

    raw_text = response.choices[0].message.content or ""
    print(f"Ответ от Groq:\n{raw_text}\n")

    title = ""
    body = ""

    if "ЗАГОЛОВОК:" in raw_text and "ТЕКСТ:" in raw_text:
        try:
            title_part = raw_text.split("ЗАГОЛОВОК:")[1].split("ТЕКСТ:")[0].strip()
            body_part = raw_text.split("ТЕКСТ:")[1].strip()
            title = title_part
            body = body_part
        except Exception:
            pass

    if not title or not body:
        title = "Интересный факт"
        body = (
            "Каждый день приносит новые открытия. "
            "Мир вокруг нас полон удивительных явлений, "
            "о которых мы часто даже не задумываемся. "
            "Например, человеческий мозг обрабатывает "
            "больше информации за один день, "
            "чем самый мощный компьютер несколько десятилетий назад. "
            "Это напоминает нам о том, как много чудесного "
            "скрыто в привычных вещах."
        )

    message = f"📌 {title}\n\n{body}"
    print(f"Итоговое сообщение:\n{message[:200]}...")

    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=channel, text=message)
    print("Пост успешно отправлен в Telegram!")

if __name__ == "__main__":
    asyncio.run(main())

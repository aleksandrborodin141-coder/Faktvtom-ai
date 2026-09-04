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
                    "Ты — креативный автор viral-контента для Telegram-канала. "
                    "Пишешь на русском языке. "
                    "Каждый пост: цепляющий заголовок (1 строка) + "
                    "3 коротких абзаца по 2-3 предложения + "
                    "итоговая мысль (1-2 предложения). "
                    "Без хештегов, без эмодзи — я добавлю их сам."
                )
            },
            {
                "role": "user",
                "content": (
                    "Напиши пост в строгом формате:\n\n"
                    "ЗАГОЛОВОК: <короткий яркий заголовок>\n"
                    "АБЗАЦ1: <первый абзац>\n"
                    "АБЗАЦ2: <второй абзац>\n"
                    "АБЗАЦ3: <третий абзац>\n"
                    "ВЫВОД: <итоговая мысль>\n\n"
                    "Тема: один интересный факт или наблюдение."
                )
            }
        ],
        max_tokens=700,
        temperature=0.8
    )

    raw_text = response.choices[0].message.content or ""
    print(f"Ответ от Groq:\n{raw_text}\n")

    title = ""
    p1 = ""
    p2 = ""
    p3 = ""
    conclusion = ""

    if "ЗАГОЛОВОК:" in raw_text:
        try:
            title = raw_text.split("ЗАГОЛОВОК:")[1].split("АБЗАЦ1:")[0].strip()
            p1 = raw_text.split("АБЗАЦ1:")[1].split("АБЗАЦ2:")[0].strip()
            p2 = raw_text.split("АБЗАЦ2:")[1].split("АБЗАЦ3:")[0].strip()
            p3 = raw_text.split("АБЗАЦ3:")[1].split("ВЫВОД:")[0].strip()
            conclusion = raw_text.split("ВЫВОД:")[1].strip()
        except Exception:
            pass

    if not title:
        title = "Удивительный факт дня"
        p1 = "Человеческий мозг обрабатывает около 70 000 мыслей каждый день."
        p2 = "При этом он потребляет всего около 20 ватт энергии."
        p3 = "Это делает наш разум самым эффективным вычислительным устройством на планете."
        conclusion = "Иногда самые мощные вещи скрываются в самых простых формах."

    # HTML-форматирование
    message = (
        f"<b>🔥 {title}</b>\n\n"
        f"─────────────────\n\n"
        f"💡 {p1}\n\n"
        f"⚡ {p2}\n\n"
        f"🧠 {p3}\n\n"
        f"─────────────────\n\n"
        f"<i>💭 {conclusion}</i>\n\n"
        f"👇 <b>Твоя реакция?</b>\n"
        f"Нажми дважды на пост и выбери эмодзи: 🔥 🤯 💡 ❤️ 👍\n\n"
        f"💬 <b>Обсудим в комментариях?</b> Жми кнопку ниже ↓\n\n"
        f"#факт #мысли #интересно #знания #мир"
    )

    print(f"Итоговое сообщение:\n{message[:300]}...")

    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=channel,
        text=message,
        parse_mode="HTML"
    )
    print("Пост успешно отправлен!")

if __name__ == "__main__":
    asyncio.run(main())

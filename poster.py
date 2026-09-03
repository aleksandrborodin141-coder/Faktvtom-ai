import os
import asyncio
from openai import OpenAI
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

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
                    "Пишешь на русском языке. Обязательно используй эмодзи "
                    "(🔥 💡 ⚡ 🧠 🌍 ✨ ❗ 🎯 🚀 🎓 🤯 🌟). "
                    "Каждый пост: цепляющий заголовок (1 строка, крупный) + "
                    "развёрнутый текст (5-8 предложений, с эмодзи). "
                    "Без хештегов в тексте."
                )
            },
            {
                "role": "user",
                "content": (
                    "Напиши пост в строгом формате:\n\n"
                    "ЗАГОЛОВОК: <эмодзи + короткий яркий заголовок>\n"
                    "ТЕКСТ: <развёрнутый текст с эмодзи>\n\n"
                    "Тема: один интересный факт, открытие или мысль, "
                    "которую захочется перечитать."
                )
            }
        ],
        max_tokens=700,
        temperature=0.9
    )

    raw_text = response.choices[0].message.content or ""
    print(f"Ответ от Groq:\n{raw_text}\n")

    title = ""
    body = ""

    if "ЗАГОЛОВОК:" in raw_text and "ТЕКСТ:" in raw_text:
        try:
            title = raw_text.split("ЗАГОЛОВОК:")[1].split("ТЕКСТ:")[0].strip()
            body = raw_text.split("ТЕКСТ:")[1].strip()
        except Exception:
            pass

    if not title or not body:
        title = "🧠 Удивительный факт дня"
        body = (
            "🔥 Человеческий мозг обрабатывает около 70 000 мыслей каждый день.\n\n"
            "⚡ При этом он потребляет всего около 20 ватт энергии — "
            "меньше, чем обычная лампочка накаливания.\n\n"
            "🌍 Это делает наш разум самым эффективным вычислительным "
            "устройством на планете, созданным природой.\n\n"
            "🚀 Интересно, что если бы мозг был компьютером, "
            "он бы занимал площадь в несколько футбольных полей, "
            "но при этом работал на энергии одной батарейки."
        )

    # Красивое оформление с рамками Unicode box-drawing
    message = (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃  {title}\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{body}\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  💬 Как тебе факт?    ┃\n"
        f"┃  👇 Поставь реакцию!  ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦ ✦\n\n"
        f"🔖 #факт #мысли #интересно #знания #мир"
    )

    # Кнопки-реакции под постом
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥", callback_data="react_fire"),
            InlineKeyboardButton("🤯", callback_data="react_mindblown"),
            InlineKeyboardButton("💡", callback_data="react_idea"),
            InlineKeyboardButton("❤️", callback_data="react_love"),
            InlineKeyboardButton("👍", callback_data="react_like")
        ]
    ])

    print(f"Итоговое сообщение:\n{message[:300]}...")

    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=channel,
        text=message,
        reply_markup=keyboard
    )
    print("Пост с реакциями успешно отправлен в Telegram!")

if __name__ == "__main__":
    asyncio.run(main())

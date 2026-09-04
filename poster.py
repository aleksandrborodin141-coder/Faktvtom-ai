import os
import asyncio
import json
import urllib.request
import urllib.parse
from openai import OpenAI
from telegram import Bot


def check_spelling_yandex(text):
    """Проверка орфографии через API Яндекс.Спеллера (без сторонних библиотек)."""
    url = "https://speller.yandex.net/services/spellservice.json/checkText"
    data = urllib.parse.urlencode({"text": text, "lang": "ru"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())

    # Применяем исправления (с конца, чтобы не сбить позиции)
    corrected = text
    for error in reversed(result):
        pos = error["pos"]
        length = error["len"]
        suggestion = error["s"][0] if error.get("s") else error["word"]
        corrected = corrected[:pos] + suggestion + corrected[pos + length:]

    return corrected


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

    # === ЭТАП 1: Генерация поста ===
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

    draft = response.choices[0].message.content or ""
    print(f"Черновик:\n{draft}\n")

    # === ЭТАП 2: Проверка через Groq-редактор ===
    proofread = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — профессиональный редактор русского языка. "
                    "Твоя задача: проверить текст на орфографические, "
                    "пунктуационные и стилистические ошибки. "
                    "Исправь всё, что найдёшь. Сохрани исходный формат "
                    "(ЗАГОЛОВОК, АБЗАЦ1, АБЗАЦ2, АБЗАЦ3, ВЫВОД). "
                    "Не добавляй эмодзи и хештеги."
                )
            },
            {
                "role": "user",
                "content": f"Проверь и исправь этот текст:\n\n{draft}"
            }
        ],
        max_tokens=800,
        temperature=0.2
    )

    after_groq = proofread.choices[0].message.content or draft
    print(f"После Groq:\n{after_groq}\n")

    # === ЭТАП 3: Проверка через Яндекс.Спеллер ===
    print("Запускаю Яндекс.Спеллер...")
    after_speller = check_spelling_yandex(after_groq)
    print(f"После Спеллера:\n{after_speller}\n")

    # === Разбор текста ===
    title = ""
    p1 = ""
    p2 = ""
    p3 = ""
    conclusion = ""

    if "ЗАГОЛОВОК:" in after_speller:
        try:
            title = after_speller.split("ЗАГОЛОВОК:")[1].split("АБЗАЦ1:")[0].strip()
            p1 = after_speller.split("АБЗАЦ1:")[1].split("АБЗАЦ2:")[0].strip()
            p2 = after_speller.split("АБЗАЦ2:")[1].split("АБЗАЦ3:")[0].strip()
            p3 = after_speller.split("АБЗАЦ3:")[1].split("ВЫВОД:")[0].strip()
            conclusion = after_speller.split("ВЫВОД:")[1].strip()
        except Exception:
            pass

    if not title:
        title = "Удивительный факт дня"
        p1 = "Человеческий мозг обрабатывает около 70 000 мыслей каждый день."
        p2 = "При этом он потребляет всего около 20 ватт энергии."
        p3 = "Это делает наш разум самым эффективным вычислительным устройством на планете."
        conclusion = "Иногда самые мощные вещи скрываются в самых простых формах."

    # === Финальное оформление ===
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

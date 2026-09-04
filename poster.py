import os
import asyncio
import json
import re
import html
import urllib.request
import urllib.parse
from openai import OpenAI
from telegram import Bot


def check_spelling_yandex(text):
    """Проверка орфографии через API Яндекс.Спеллера."""
    url = "https://speller.yandex.net/services/spellservice.json/checkText"
    data = urllib.parse.urlencode({"text": text, "lang": "ru"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())

    corrected = text
    for error in reversed(result):
        pos = error["pos"]
        length = error["len"]
        suggestion = error["s"][0] if error.get("s") else error["word"]
        corrected = corrected[:pos] + suggestion + corrected[pos + length:]

    return corrected


def parse_post(text):
    """Гибкий парсер: убирает метки АБЗАЦ/ВЫВОД и извлекает чистый контент."""
    cleaned = re.sub(r'(?i)(заголовок|абзац\s*\d|вывод)[\s:]*', '', text)
    paragraphs = [p.strip() for p in cleaned.split('\n') if p.strip()]
    
    if len(paragraphs) >= 5:
        return paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3], paragraphs[4]
    elif len(paragraphs) >= 4:
        return paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3]
    elif len(paragraphs) >= 2:
        return paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[1], paragraphs[-1]
    else:
        return "Интересный факт", "Факт дня", "Удивительное открытие", "Новые знания", "Думайте об этом."


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

    # === ЭТАП 1: Генерация ===
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — автор Telegram-канала. Пиши на русском языке. "
                    "Формат поста (строго 5 строк, разделённых переносом строки):\n"
                    "1. Заголовок — 1 короткая строка\n"
                    "2. Абзац 1 — 2-3 предложения\n"
                    "3. Абзац 2 — 2-3 предложения\n"
                    "4. Абзац 3 — 2-3 предложения\n"
                    "5. Вывод — 1-2 предложения\n\n"
                    "НЕ пиши слова 'АБЗАЦ', 'ВЫВОД', 'ЗАГОЛОВОК' в тексте. "
                    "Только чистый текст, без спецсимволов < > &."
                )
            },
            {
                "role": "user",
                "content": "Напиши интересный факт для Telegram-канала. 5 строк текста, без служебных меток."
            }
        ],
        max_tokens=700,
        temperature=0.8
    )

    draft = response.choices[0].message.content or ""
    print(f"Черновик:\n{draft}\n")

    # === ЭТАП 2: Редактура Groq ===
    proofread = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — редактор русского языка. Проверь орфографию и пунктуацию. "
                    "Сохрани формат: 5 строк текста, без меток 'АБЗАЦ', 'ВЫВОД'."
                )
            },
            {"role": "user", "content": draft}
        ],
        max_tokens=800,
        temperature=0.2
    )

    after_groq = proofread.choices[0].message.content or draft
    print(f"После Groq:\n{after_groq}\n")

    # === ЭТАП 3: Яндекс.Спеллер ===
    print("Запускаю Яндекс.Спеллер...")
    after_speller = check_spelling_yandex(after_groq)
    print(f"После Спеллера:\n{after_speller}\n")

    # === Разбор ===
    title, p1, p2, p3, conclusion = parse_post(after_speller)
    print(f"Заголовок: {title}")
    print(f"Абзац 1: {p1[:50]}...")
    print(f"Абзац 2: {p2[:50]}...")
    print(f"Абзац 3: {p3[:50]}...")
    print(f"Вывод: {conclusion}")

    # === Финальное оформление (с экранированием HTML) ===
    message = (
        f"<b>🔥 {html.escape(title)}</b>\n\n"
        f"─────────────────\n\n"
        f"💡 {html.escape(p1)}\n\n"
        f"⚡ {html.escape(p2)}\n\n"
        f"🧠 {html.escape(p3)}\n\n"
        f"─────────────────\n\n"
        f"<i>💭 {html.escape(conclusion)}</i>\n\n"
        f"👇 <b>Твоя реакция?</b>\n"
        f"Нажми дважды на пост и выбери эмодзи: 🔥 🤯 💡 ❤️ 👍\n\n"
        f"💬 <b>Обсудим в комментариях?</b> Жми кнопку ниже ↓\n\n"
        f"#факт #мысли #интересно #знания #мир"
    )

    print(f"Итог:\n{message[:300]}...")

    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=channel,
        text=message,
        parse_mode="HTML"
    )
    print("Пост отправлен!")

if __name__ == "__main__":
    asyncio.run(main())

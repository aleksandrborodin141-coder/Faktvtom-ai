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


def smart_parse(text):
    if not text or not text.strip():
        return None
    cleaned = re.sub(r'(?i)\b(заголовок|абзац\s*\d+|вывод)[\s:]*', '', text)
    cleaned = cleaned.strip()
    paragraphs = [p.strip() for p in cleaned.split('\n') if p.strip()]
    if len(paragraphs) < 2:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
        paragraphs = sentences
    print(f"Найдено частей: {len(paragraphs)}")
    if len(paragraphs) >= 5:
        return [paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3], paragraphs[4]]
    elif len(paragraphs) == 4:
        return [paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3]]
    elif len(paragraphs) == 3:
        return [paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[2]]
    elif len(paragraphs) == 2:
        return [paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[1], paragraphs[1]]
    elif len(paragraphs) == 1:
        return [paragraphs[0], paragraphs[0], paragraphs[0], paragraphs[0], paragraphs[0]]
    return None


def get_fallback():
    """Возвращает список из 5 строк — гарантированно."""
    return [
        "Тайны океанских глубин",
        "Более 80% океана Земли остаётся неизученным.",
        "Учёные знают о дне Марсианских кратеров больше, чем о дне Тихого океана.",
        "Каждый год в океане обнаруживают около 2 000 новых видов животных.",
        "Может, самые невероятные открытия ждут нас прямо под ногами?"
    ]


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

    client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")

    # === ЭТАП 1: Генерация с retry ===
    draft = ""
    for attempt in range(1, 4):
        try:
            print(f"Попытка генерации {attempt}/3...")
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — автор Telegram-канала. Пиши на русском. "
                            "5 строк текста, каждая с новой строки:\n"
                            "1. Заголовок\n"
                            "2. Абзац 1 (2-3 предложения)\n"
                            "3. Абзац 2 (2-3 предложения)\n"
                            "4. Абзац 3 (2-3 предложения)\n"
                            "5. Вывод (1-2 предложения)\n"
                            "БЕЗ слов 'АБЗАЦ', 'ВЫВОД', 'ЗАГОЛОВОК'."
                        )
                    },
                    {
                        "role": "user",
                        "content": "Напиши интересный факт. Ровно 5 строк."
                    }
                ],
                max_tokens=700,
                temperature=0.8
            )
            draft = response.choices[0].message.content or ""
            print(f"Получено {len(draft)} символов")
            if draft.strip():
                break
        except Exception as e:
            print(f"Ошибка попытки {attempt}: {e}")
            await asyncio.sleep(3)

    print(f"Черновик:\n{draft}\n")

    # === ЭТАП 2: Редактура ===
    after_groq = draft
    if draft.strip():
        try:
            proofread = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Проверь орфографию. Сохрани 5 строк."},
                    {"role": "user", "content": draft}
                ],
                max_tokens=800,
                temperature=0.2
            )
            after_groq = proofread.choices[0].message.content or draft
        except Exception as e:
            print(f"Ошибка редактуры: {e}")

    print(f"После Groq ({len(after_groq)} символов):\n{after_groq}\n")

    # === ЭТАП 3: Спеллер ===
    after_speller = after_groq
    try:
        print("Запускаю Яндекс.Спеллер...")
        after_speller = check_spelling_yandex(after_groq)
    except Exception as e:
        print(f"Ошибка спеллера: {e}")

    print(f"После Спеллера ({len(after_speller)} символов):\n{after_speller}\n")

    # === Разбор ===
    parsed = smart_parse(after_speller)
    if parsed:
        parts = parsed
        print("Парсер сработал.")
    else:
        print("Парсер не справился. Fallback.")
        parts = get_fallback()

    title = parts[0]
    p1 = parts[1]
    p2 = parts[2]
    p3 = parts[3]
    conclusion = parts[4]

    print(f"\nЗаголовок: {title}")
    print(f"Абзац 1: {p1[:50]}...")
    print(f"Абзац 2: {p2[:50]}...")
    print(f"Абзац 3: {p3[:50]}...")
    print(f"Вывод: {conclusion}")

    # === Отправка ===
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

    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=channel, text=message, parse_mode="HTML")
    print("Пост отправлен!")

if __name__ == "__main__":
    asyncio.run(main())

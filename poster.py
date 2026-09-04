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


def smart_parse(text):
    """Умный парсер: работает с любым форматом от Groq."""
    if not text or not text.strip():
        return None

    # Убираем служебные метки
    cleaned = re.sub(r'(?i)\b(заголовок|абзац\s*\d+|вывод)[\s:]*', '', text)
    cleaned = cleaned.strip()

    # Разбиваем на абзацы по переносам строк
    paragraphs = [p.strip() for p in cleaned.split('\n') if p.strip()]

    # Если переносов нет — разбиваем по точкам (предложения)
    if len(paragraphs) < 2:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
        paragraphs = sentences

    print(f"Найдено абзацев/предложений: {len(paragraphs)}")

    if len(paragraphs) >= 5:
        return paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3], paragraphs[4]
    elif len(paragraphs) == 4:
        return paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[3]
    elif len(paragraphs) == 3:
        return paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[2], paragraphs[2]
    elif len(paragraphs) == 2:
        return paragraphs[0], paragraphs[0], paragraphs[1], paragraphs[1], paragraphs[1]
    elif len(paragraphs) == 1:
        return paragraphs[0], paragraphs[0], paragraphs[0], paragraphs[0], paragraphs[0]
    else:
        return None


def fallback_fact():
    """Реальный интересный факт на случай, если Groq не ответил."""
    return (
        "Тайны океанских глубин",
        "Более 80% океана Земли остаётся неизученным.",
        "Учёные знают о дне Марсианских кратеров больше, чем о дне Тихого океана.",
        "Каждый год в океане обнаруживают около 2 000 новых видов животных.",
        "Глубже мы знаем космос, чем собственный океан.",
        "Может, самые невероятные открытия ждут нас прямо под ногами?"
    )


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
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — автор Telegram-канала. Пиши на русском языке. "
                        "Создай пост из 5 частей, каждая с новой строки:\n"
                        "1. Короткий заголовок\n"
                        "2. Первый абзац (2-3 предложения)\n"
                        "3. Второй абзац (2-3 предложения)\n"
                        "4. Третий абзац (2-3 предложения)\n"
                        "5. Короткий вывод (1-2 предложения)\n\n"
                        "НЕ пиши слова 'АБЗАЦ', 'ВЫВОД', 'ЗАГОЛОВОК'. "
                        "Только чистый текст."
                    )
                },
                {
                    "role": "user",
                    "content": "Напиши интересный факт. Раздели на 5 строк."
                }
            ],
            max_tokens=700,
            temperature=0.8
        )
        draft = response.choices[0].message.content or ""
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        draft = ""

    print(f"Черновик ({len(draft)} символов):\n{draft}\n")

    # Если Groq вернул пустоту — используем fallback
    if not draft.strip():
        print("Groq вернул пустой ответ. Использую fallback.")
        title, p1, p2, p3, conclusion = fallback_fact()
    else:
        # === ЭТАП 2: Редактура Groq ===
        try:
            proofread = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": "Проверь орфографию. Сохрани 5 строк текста."
                    },
                    {"role": "user", "content": draft}
                ],
                max_tokens=800,
                temperature=0.2
            )
            after_groq = proofread.choices[0].message.content or draft
        except Exception as e:
            print(f"Ошибка редактуры: {e}")
            after_groq = draft

        print(f"После Groq ({len(after_groq)} символов):\n{after_groq}\n")

        # === ЭТАП 3: Яндекс.Спеллер ===
        try:
            print("Запускаю Яндекс.Спеллер...")
            after_speller = check_spelling_yandex(after_groq)
        except Exception as e:
            print(f"Ошибка спеллера: {e}")
            after_speller = after_groq

        print(f"После Спеллера ({len(after_speller)} символов):\n{after_speller}\n")

        # === Разбор ===
        parsed = smart_parse(after_speller)

        if parsed:
            title, p1, p2, p3, conclusion = parsed
        else:
            print("Парсер не справился. Использую fallback.")
            title, p1, p2, p3, conclusion = fallback_fact()

    print(f"\n=== ФИНАЛЬНЫЙ ПОСТ ===")
    print(f"Заголовок: {title}")
    print(f"Абзац 1: {p1[:60]}...")
    print(f"Абзац 2: {p2[:60]}...")
    print(f"Абзац 3: {p3[:60]}...")
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
    await bot.send_message(
        chat_id=channel,
        text=message,
        parse_mode="HTML"
    )
    print("\nПост успешно отправлен!")

if __name__ == "__main__":
    asyncio.run(main())
    

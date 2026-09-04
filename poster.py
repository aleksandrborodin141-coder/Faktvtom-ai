import os
import asyncio
import json
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


def generate_image(prompt, filename="image.jpg"):
    """Генерация картинки через Pollinations.ai."""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
    
    print(f"Генерирую картинку: {prompt[:60]}...")
    
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "Mozilla/5.0")
    
    with urllib.request.urlopen(req, timeout=60) as response:
        with open(filename, "wb") as f:
            f.write(response.read())
    
    print(f"Картинка сохранена: {filename}")
    return filename


def get_fallback():
    return {
        "title": "Тайны океанских глубин",
        "p1": "Более 80% океана Земли остаётся неизученным.",
        "p2": "Учёные знают о дне Марсианских кратеров больше, чем о дне Тихого океана.",
        "p3": "Каждый год в океане обнаруживают около 2 000 новых видов животных.",
        "conclusion": "Может, самые невероятные открытия ждут нас прямо под ногами?",
        "image_prompt": "deep ocean underwater mysterious creatures blue water realistic photo"
    }


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

    # === ЭТАП 1: Генерация JSON с английским промптом для картинки ===
    draft_json = None
    for attempt in range(1, 4):
        try:
            print(f"Попытка генерации {attempt}/3...")
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — автор Telegram-канала. Пиши на русском языке. "
                            "Ответь строго в формате JSON с полями: "
                            "title (заголовок на русском), "
                            "p1 (абзац 1), p2 (абзац 2), p3 (абзац 3), "
                            "conclusion (вывод), "
                            "image_prompt (короткое описание картинки на АНГЛИЙСКОМ, 5-7 слов, для генерации фото). "
                            "Абзацы — 2-3 предложения. Без эмодзи."
                        )
                    },
                    {
                        "role": "user",
                        "content": "Напиши интересный факт. Ответь только JSON."
                    }
                ],
                max_tokens=800,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or ""
            print(f"Получено {len(raw)} символов")
            if raw.strip():
                draft_json = json.loads(raw)
                required = ["title", "p1", "p2", "p3", "conclusion", "image_prompt"]
                if all(k in draft_json and draft_json[k].strip() for k in required):
                    break
                else:
                    print(f"JSON неполный. Поля: {list(draft_json.keys())}")
        except Exception as e:
            print(f"Ошибка попытки {attempt}: {e}")
            await asyncio.sleep(3)

    if not draft_json:
        print("Groq не справился. Fallback.")
        draft_json = get_fallback()

    # === ЭТАП 2: Редактура ===
    try:
        proofread = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — редактор. Проверь орфографию. "
                        "Ответь в JSON: title, p1, p2, p3, conclusion, image_prompt."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(draft_json, ensure_ascii=False)
                }
            ],
            max_tokens=900,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        after_groq = json.loads(proofread.choices[0].message.content or "{}")
        required = ["title", "p1", "p2", "p3", "conclusion", "image_prompt"]
        if all(k in after_groq and after_groq[k].strip() for k in required):
            draft_json = after_groq
    except Exception as e:
        print(f"Ошибка редактуры: {e}")

    # === ЭТАП 3: Яндекс.Спеллер ===
    try:
        print("Запускаю Яндекс.Спеллер...")
        for key in ["title", "p1", "p2", "p3", "conclusion"]:
            draft_json[key] = check_spelling_yandex(draft_json[key])
    except Exception as e:
        print(f"Ошибка спеллера: {e}")

    title = draft_json["title"]
    p1 = draft_json["p1"]
    p2 = draft_json["p2"]
    p3 = draft_json["p3"]
    conclusion = draft_json["conclusion"]
    image_prompt = draft_json["image_prompt"]

    print(f"\nЗаголовок: {title}")
    print(f"Промпт для картинки: {image_prompt}")

    # === ЭТАП 4: Генерация картинки ===
    image_path = None
    try:
        full_prompt = f"{image_prompt}, realistic photo, high quality, detailed, cinematic lighting"
        image_path = generate_image(full_prompt, "post_image.jpg")
    except Exception as e:
        print(f"Не удалось сгенерировать картинку: {e}")

    # === Отправка ===
    caption = (
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

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await bot.send_photo(
                chat_id=channel,
                photo=photo,
                caption=caption,
                parse_mode="HTML"
            )
        print("Пост с картинкой отправлен!")
    else:
        await bot.send_message(chat_id=channel, text=caption, parse_mode="HTML")
        print("Пост без картинки отправлен!")

if __name__ == "__main__":
    asyncio.run(main())

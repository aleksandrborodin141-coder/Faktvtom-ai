import os
import asyncio
import json
import html
import random
import re
import urllib.request
import urllib.parse
from openai import OpenAI
from telegram import Bot

# === Пул тем (разнообразие) ===
TOPICS = [
    "редкое животное, о котором мало кто знает",
    "необычная традиция в другой стране",
    "забытое изобретение прошлого",
    "парадокс в физике или математике",
    "тайна древней цивилизации",
    "неожиданное свойство обычной еды",
    "факт о языках и общении",
    "загадка человеческого тела",
    "история одного предмета быта",
    "космический объект, о котором редко пишут",
    "необычная профессия в мире",
    "факт о погоде и климате",
    "историческая личность и её странная привычка",
    "факт о деньгах и экономике",
    "неожиданное применение технологии",
    "загадка архитектуры",
    "необычный рекорд Гиннесса",
    "тайна из мира искусства",
    "факт о животных-альтруистах",
    "история создания обычного слова",
    "неожиданная связь между двумя странами",
    "факт о цвете и восприятии",
    "загадка подземного мира",
    "необычный судебный процесс в истории",
    "факт о музыке и мозге",
    "тайна заброшенного места",
    "неожиданное свойство льда или огня",
    "история одного числа или даты",
    "факт о запахах и обонянии",
    "необычный способ лечения в прошлом",
    "факт о древних технологиях",
    "неожиданная правда о привычке",
]

# === Проверенные реальные факты (fallback) ===
REAL_FACTS = [
    {
        "title": "Бессмертная медуза",
        "p1": "В Тихом океане обитает медуза Turritopsis dohrnii, которая способна возвращаться к стадии полипа при повреждении или старении.",
        "p2": "Этот процесс называется трансдифференцировкой — клетки медузы перепрограммируются, и она начинает жизнь заново.",
        "p3": "Теоретически такой цикл может повторяться бесконечно, что делает этот вид биологически бессмертным.",
        "conclusion": "Природа нашла способ обманывать смерть задолго до того, как о нем задумались учёные.",
        "image_prompt": "immortal jellyfish underwater glowing blue ocean realistic",
    },
    {
        "title": "Розовое озеро Австралии",
        "p1": "На острове Миддл в Западной Австралии находится озеро Хиллиер, вода в котором имеет ярко-розовый цвет круглый год.",
        "p2": "Причиной окраски являются микроорганизмы — красные водоросли Dunaliella salina и розовые бактерии.",
        "p3": "Несмотря на экзотический вид, вода в озере абсолютно безопасна для плавания, хотя и очень солёная.",
        "conclusion": "Иногда самые невероятные цвета природы скрываются в простых микроорганизмах.",
        "image_prompt": "pink lake Hillier Australia aerial view vibrant realistic",
    },
    {
        "title": "Три сердца осьминога",
        "p1": "Осьминоги обладают тремя сердцами: два перекачивают кровь через жабры, а третье — по всему телу.",
        "p2": "Их кровь синего цвета из-за медсодержащего белка гемоцианина, который эффективнее переносит кислород в холодной воде.",
        "p3": "Во время плавания основное сердце останавливается, поэтому осьминоги предпочитают ползать по дну.",
        "conclusion": "Эволюция создала для осьминогов совершенно иную биологию, чем для позвоночных.",
        "image_prompt": "octopus underwater three hearts blue blood realistic photo",
    },
    {
        "title": "Остров кошек Аосима",
        "p1": "В Японии есть небольшой остров Аосима, где кошек в шесть раз больше, чем людей.",
        "p2": "Когда-то рыбаки завезли кошек для борьбы с грызунами на кораблях, а со временем популяция разрослась.",
        "p3": "Сейчас остров стал популярным туристическим объектом, хотя инфраструктура там минимальна.",
        "conclusion": "Иногда небольшое человеческое решение способно изменить ландшафт целого острова.",
        "image_prompt": "Aoshima cat island Japan many cats street realistic",
    },
    {
        "title": "Венера вращается вспять",
        "p1": "Венера — единственная планета Солнечной системы, которая вращается в обратную сторону по сравнению с большинством других.",
        "p2": "Сутки на Венере длиннее года: полный оборот вокруг оси занимает 243 земных суток, а год — 225.",
        "p3": "Учёные связывают ретроградное вращение с древним столкновением с крупным небесным телом.",
        "conclusion": "Космос хранит следы катаклизмов, которые произошли миллиарды лет назад.",
        "image_prompt": "Venus planet retrograde rotation space realistic",
    },
    {
        "title": "Отпечатки коалы",
        "p1": "Отпечатки пальцев коалы настолько похожи на человеческие, что даже эксперты с трудом отличают их под микроскопом.",
        "p2": "Это пример конвергентной эволюции — у приматов и коал схожая структура пальцев развилась независимо друг от друга.",
        "p3": "В прошлом следы коал даже вводили в заблуждение криминалистов на местах преступлений в Австралии.",
        "conclusion": "Природа иногда находит одинаковые решения для схожих задач в совершенно разных ветвях жизни.",
        "image_prompt": "koala paw fingerprints close up realistic nature",
    },
    {
        "title": "Самый старый организм",
        "p1": "В Калифорнии растет сосна Мафусаил, возраст которой превышает 4800 лет — она была посажена за 2800 лет до нашей эры.",
        "p2": "Дерево пережило египетских фараонов, постройку пирамид и падение Римской империи.",
        "p3": "Точное местоположение сосны засекречено, чтобы защитить её от вандалов и туристов.",
        "conclusion": "В мире есть живые свидетели истории, которые помнят времена, когда человечество только начинало писать.",
        "image_prompt": "ancient bristlecone pine tree Methuselah old gnarled realistic",
    },
    {
        "title": "Глаз страуса",
        "p1": "Глаз страуса имеет диаметр около 5 сантиметров — это больше, чем его мозг.",
        "p2": "Такие огромные глаза позволяют птице видеть предметы на расстоянии до 3,5 километров.",
        "p3": "При этом страус не прячет голову в песок — это миф. Вместо этого он ложится на землю, чтобы стать менее заметным.",
        "conclusion": "Некоторые «факты», которые мы знаем с детства, оказываются выдумкой, а реальность — ещё удивительнее.",
        "image_prompt": "ostrich big eye close up African savanna realistic",
    },
    {
        "title": "Водопады крови Антарктиды",
        "p1": "В Антарктиде существуют «кровавые водопады» — потоки солёной воды, насыщенной оксидом железа, вытекающие из ледника.",
        "p2": "Эта вода была изолирована от внешнего мира около 2 миллионов лет и не содержит кислорода.",
        "p3": "Несмотря на экстремальные условия, в этой воде обнаружены уникальные микроорганизмы, которые питаются сульфатами и железом.",
        "conclusion": "Жизнь способна существовать там, где человек видит только смерть и холод.",
        "image_prompt": "Blood Falls Antarctica red waterfall ice glacier realistic",
    },
    {
        "title": "Муравьи без сна",
        "p1": "Муравьи практически не спят в привычном понимании этого слова — вместо этого они делают сотни микро-перерывов по одной минуте.",
        "p2": "Королева муравьёв отдыхает чуть дольше, но и она не имеет полноценного сна.",
        "p3": "Исследования показали, что рабочие муравьи могут бодрствовать до нескольких недель без видимого ущерба для организма.",
        "conclusion": "Для некоторых существ время — ресурс, который можно тратить совершенно иначе, чем мы привыкли.",
        "image_prompt": "ants colony macro close up working realistic nature",
    },
]


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
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(1,9999)}"
    print(f"Генерирую картинку: {prompt[:60]}...")
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=60) as response:
        with open(filename, "wb") as f:
            f.write(response.read())
    print(f"Картинка сохранена: {filename}")
    return filename


def is_text_valid(text):
    """Проверяем, что текст не бред и не слишком короткий."""
    if not text or len(text) < 30:
        return False
    # Проверяем на повторы одного символа (бред)
    if re.search(r'(.)\1{10,}', text):
        return False
    # Проверяем, что есть русские буквы
    if not re.search(r'[а-яА-Я]', text):
        return False
    return True


def get_fallback_fact():
    return random.choice(REAL_FACTS)


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

    topic = random.choice(TOPICS)
    print(f"Тема: {topic}")

    draft_json = None

    # === ЭТАП 1: Генерация ===
    for attempt in range(1, 4):
        try:
            print(f"Попытка генерации {attempt}/3...")
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — автор научно-популярного Telegram-канала. "
                            "Пиши ТОЛЬКО проверенные научные или исторические факты. "
                            "Не выдумывай детали, даты и имена. "
                            "Если точная цифра неизвестна — не пиши её. "
                            "Ответь строго в JSON: title, p1, p2, p3, conclusion, image_prompt (английский, 5-7 слов). "
                            f"Тема: {topic}. Абзацы — 2-3 предложения. Без эмодзи."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Напиши проверенный факт на тему: {topic}. Только JSON."
                    }
                ],
                max_tokens=900,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content or ""
            print(f"Получено {len(raw)} символов")
            if raw.strip():
                draft_json = json.loads(raw)
                required = ["title", "p1", "p2", "p3", "conclusion", "image_prompt"]
                if all(k in draft_json and draft_json[k].strip() for k in required):
                    # Проверяем адекватность каждого поля
                    if all(is_text_valid(draft_json[k]) for k in required):
                        break
                    else:
                        print("Текст неадекватный, пробую ещё...")
                else:
                    print(f"JSON неполный. Поля: {list(draft_json.keys())}")
        except Exception as e:
            print(f"Ошибка попытки {attempt}: {e}")
            await asyncio.sleep(3)

    if not draft_json:
        print("Groq не справился. Fallback.")
        draft_json = get_fallback_fact()

    # === ЭТАП 2: Fact-check через Groq ===
    fact_score = 0
    try:
        print("Проверяю достоверность факта...")
        check_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт по проверке фактов. "
                        "Оцени достоверность текста ниже по шкале от 1 до 10. "
                        "10 — абсолютно проверенный научный факт. "
                        "1 — явная выдумка или бред. "
                        "Ответь ТОЛЬКО числом от 1 до 10, без текста."
                    )
                },
                {
                    "role": "user",
                    "content": f"Заголовок: {draft_json['title']}\n\nТекст:\n{draft_json['p1']}\n{draft_json['p2']}\n{draft_json['p3']}"
                }
            ],
            max_tokens=10,
            temperature=0.1
        )
        score_text = check_response.choices[0].message.content.strip()
        # Извлекаем число
        match = re.search(r'\d+', score_text)
        if match:
            fact_score = int(match.group())
        print(f"Оценка достоверности: {fact_score}/10")
    except Exception as e:
        print(f"Ошибка fact-check: {e}")

    # Если факт сомнителен — берём проверенный fallback
    if fact_score < 6:
        print(f"Факт сомнителен ({fact_score}/10). Заменяю на проверенный.")
        draft_json = get_fallback_fact()

    # === ЭТАП 3: Редактура ===
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

    # === ЭТАП 4: Яндекс.Спеллер ===
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
    print(f"Промпт: {image_prompt}")

    # === ЭТАП 5: Картинка ===
    image_path = None
    try:
        full_prompt = f"{image_prompt}, realistic photo, high quality, detailed, cinematic lighting"
        image_path = generate_image(full_prompt, "post_image.jpg")
    except Exception as e:
        print(f"Картинка не сгенерировалась: {e}")

    # === Отправка ===
    caption = (
        f"<b>🔥 {html.escape(title)}</b>\n\n"
        f"─────────────────\n\n"
        f"💡 {html.escape(p1)}\n\n"
        f"⚡ {html.escape(p2)}\n\n"
        f"🧠 {html.escape(p3)}\n\n"
        f"─────────────────\n\n"
        f"<i>💭 {html.escape(conclusion)}</i>\n\n"
        f"📌 <b>Факт проверен</b>\n"
        f"👇 <b>Твоя реакция?</b> Нажми дважды на пост: 🔥 🤯 💡 ❤️ 👍\n\n"
        f"💬 <b>Обсудим в комментариях?</b> Жми кнопку ниже ↓\n\n"
        f"#факт #мысли #интересно #знания #мир"
    )

    bot = Bot(token=bot_token)
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await bot.send_photo(chat_id=channel, photo=photo, caption=caption, parse_mode="HTML")
        print("Пост с картинкой отправлен!")
    else:
        await bot.send_message(chat_id=channel, text=caption, parse_mode="HTML")
        print("Пост без картинки отправлен!")

if __name__ == "__main__":
    asyncio.run(main())

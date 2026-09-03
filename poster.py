import os,asyncio
from telegram import Bot
from openai import OpenAI
async def main():
 c=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
 r=c.chat.completions.create(model="gpt-40-mini",messages=[{"role":"user","content":"Напиши один короткий интересный научный факт на русском языке (максимум 800 символов). Добавь эмодзи."}])
 t=r.choices[0].message.content
 b=Bot(os.getenv("TELEGRAM_BOT_TOKEN"))
 await b.send_message(os.getenv("CHANNEL_USERNAME"),t)
 print("✅ Пост отправлен!")
asyncio.run(main())

import os
import telebot
from groq import Groq

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groqclient = Groq(apikey=GROQ_API_KEY)

@bot.messagehandler(commands=['start'])
def sendwelcome(message):
    bot.replyto(message, "Привет! Я Руся — твой личный ИИ-помощник. Задавай любой вопрос, я на всё отвечу!")

@bot.messagehandler(func=lambda message: True)
def handlemessage(message):
    try:
        bot.sendchataction(message.chat.id, 'typing')

        chatcompletion = groqclient.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Тебя зовут Руся. Ты умный, дружелюбный и общительный ИИ-помощник. Отвечай кратко, понятно и по делу."
                },
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        response = chatcompletion.choices[0].message.content
        bot.replyto(message, response)

    except Exception as e:
        bot.replyto(message, "Ой, у меня произошла небольшая ошибка. Попробуй еще раз!")
        print(f"Error: {e}")

if name == 'main':
    print("Руся запущен и ready!")
    bot.infinitypolling()


import os
import telebot
from groq import Groq

# Берем ключи
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я Руся — твой ИИ-помощник! Задавай любой вопрос.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')

        # Запрос к нейросети
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )

        response = completion.choices[0].message.content
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, "Ой, произошла ошибка. Попробуй еще раз!")
        print(f"Error: {e}")

if __name__ == '__main__':
    print("Руся запущен!")
    bot.infinity_polling()



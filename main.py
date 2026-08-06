import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from groq import Groq

# --- НАСТРОЙКА КЛЮЧЕЙ И КЛИЕНТОВ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572244100:AAHmOgxdaek-OzqeNnxPRGQp7dnjO4mn3DQ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and "ТВОЙ" not in GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "Ты Руся — ровный, четкий, позитивный пацан. Разговариваешь на простом пацанском языке (свояк, бро, братан), "
    "но даешь точные ответы. Отвечаешь в мужском роде."
)

user_histories = {}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧹 Очистить память"), types.KeyboardButton("🎭 Сменить вайб"))
    markup.row(types.KeyboardButton("ℹ️ Кто ты?"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_histories[message.chat.id] = []
    bot.reply_to(message, "Здорово! Я Руся на связи. Погнали!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🧹 Очистить память")
def clear_memory(message):
    user_histories[message.chat.id] = []
    bot.reply_to(message, "Забыл всё! Начинаем заново. 🧹", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "ℹ️ Кто ты?")
def about_bot(message):
    bot.reply_to(message, "Я **Руся** — твой ИИ-бро на базе Llama 3! 😎", parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎭 Сменить вайб")
def change_vibe(message):
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🤙 Пацанский", callback_data="vibe_normal"))
    inline_kb.add(types.InlineKeyboardButton("🧠 Эксперт", callback_data="vibe_expert"))
    inline_kb.add(types.InlineKeyboardButton("⚡ Коротко", callback_data="vibe_short"))
    bot.reply_to(message, "Выбери вайб:", reply_markup=inline_kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vibe_"))
def handle_vibe(call):
    chat_id = call.message.chat.id
    if call.data == "vibe_normal":
        user_histories[f"prompt_{chat_id}"] = SYSTEM_PROMPT
        bot.send_message(chat_id, "Вайб: Пацанский 🤙")
    elif call.data == "vibe_expert":
        user_histories[f"prompt_{chat_id}"] = "Ты эксперт. Отвечай строго и грамотно."
        bot.send_message(chat_id, "Вайб: Эксперт 🧠")
    elif call.data == "vibe_short":
        user_histories[f"prompt_{chat_id}"] = "Отвечай максимально коротко, в 1-2 предложения."
        bot.send_message(chat_id, "Вайб: Коротко ⚡")
    user_histories[chat_id] = []
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if not groq_client:
        bot.reply_to(message, "Ошибка: Не задан GROQ_API_KEY в коде!")
        return
    try:
        bot.send_chat_action(chat_id, 'typing')
        if chat_id not in user_histories:
            user_histories[chat_id] = []

        prompt = user_histories.get(f"prompt_{chat_id}", SYSTEM_PROMPT)
        user_histories[chat_id].append({"role": "user", "content": message.text})
        if len(user_histories[chat_id]) > 4:
            user_histories[chat_id] = user_histories[chat_id][-4:]

        res = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": prompt}] + user_histories[chat_id],
            max_tokens=600
        )
        ans = res.choices[0].message.content
        user_histories[chat_id].append({"role": "assistant", "content": ans})
        bot.reply_to(message, ans, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Ой, братан, что-то пошло не так. Спроси еще раз!")

# --- ВЕБ-СЕРВЕР (ФИКС ДЛЯ FREE WEB SERVICE) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    # Render передает PORT=10000. Если нет — берем 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    print(f"Сервер слушает порт {port}...")
    server.serve_forever()

if __name__ == '__main__':
    # Сначала открываем порт для Render!
    threading.Thread(target=run_server, daemon=True).start()
    
    # Очищаем зависшие подключения
    try:
        bot.remove_webhook()
    except:
        pass

    print("Руся запущен!")
    bot.infinity_polling(skip_pending=True)

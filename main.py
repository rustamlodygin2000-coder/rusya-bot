import os
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from groq import Groq

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572244100:AAHmOgxdaek-OzqeNnxPRGQp7dnjO4mn3DQ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
CHANNEL_USERNAME = "@rusya_ai"
WEBAPP_URL = "https://rusya-bot.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and "ТВОЙ" not in GROQ_API_KEY else None

SYSTEM_PROMPT = "Ты Руся — живой, понимающий, душевный и умный бро. Разговариваешь на нормальном, классном русском языке с пацанским вайбом. Сам всегда отвечаешь В МУЖСКОМ РОДЕ. Отлично понимаешь сленг и эмоциональный контекст."
user_histories = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True

def send_sub_request(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Подписаться на Руся AI", url="https://t.me/rusya_ai"))
    markup.add(types.InlineKeyboardButton("✅ Я подписался!", callback_data="check_sub"))
    text = "👋 Здорово, свояк!\n\nЧтобы базарить со мной, надо сначала подписаться на наш официальный канал:\nhttps://t.me/rusya_ai\n\nПодпишись и жми кнопку «Я подписался!» ниже 👇"
    bot.send_message(chat_id, text, reply_markup=markup)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    app_button = types.KeyboardButton("🔮 Шар Судьбы от Руси 🔮", web_app=types.WebAppInfo(url=WEBAPP_URL))
    markup.row(app_button)
    markup.row(types.KeyboardButton("🧹 Очистить память"), types.KeyboardButton("🎭 Сменить вайб"))
    markup.row(types.KeyboardButton("ℹ️ Кто ты?"))
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    user_histories[message.chat.id] = []
    bot.reply_to(message, "Здорово! Я Руся на связи. Напиши мне что-нибудь или открывай 🔮 Шар Судьбы!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        bot.answer_callback_query(call.id, "Красава, подписка есть! 🔥")
        bot.send_message(chat_id, "Отлично, подписка зачтена! Чем помочь, бро?", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Ты еще не подписался на канал!", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "🧹 Очистить память")
def clear_memory(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    user_histories[message.chat.id] = []
    bot.reply_to(message, "Забыл всё! Начинаем заново с чистого листа. 🧹", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "ℹ️ Кто ты?")
def about_bot(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    bot.reply_to(message, "Я Руся — твой ИИ-бро на базе Llama 3.3 70B! 🔥 Заходи в 🔮 «Шар Судьбы» — узнай предсказание на сегодня!", parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎭 Сменить вайб")
def change_vibe(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    inline_kb = types.InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        types.InlineKeyboardButton("🤙 Пацанский", callback_data="vibe_normal"),
        types.InlineKeyboardButton("🔞 Режим 18+", callback_data="vibe_18"),
        types.InlineKeyboardButton("🤬 Матершинник", callback_data="vibe_materik"),
        types.InlineKeyboardButton("👑 Хвастун / Мажор", callback_data="vibe_rich"),
        types.InlineKeyboardButton("🧙‍♂️ Дед Руся", callback_data="vibe_ded"),
        types.InlineKeyboardButton("📜 Поэт", callback_data="vibe_poet"),
        types.InlineKeyboardButton("🤪 Глупый Руся", callback_data="vibe_stupid"),
        types.InlineKeyboardButton("🔬 Ученый", callback_data="vibe_science"),
        types.InlineKeyboardButton("🧬 Биолог", callback_data="vibe_biolog"),
        types.InlineKeyboardButton("🧠 Эксперт", callback_data="vibe_expert"),
        types.InlineKeyboardButton("🕵️‍♂️ Детектив", callback_data="vibe_detective"),
        types.InlineKeyboardButton("⚡ Коротко", callback_data="vibe_short")
    )
    bot.reply_to(message, "Выбирай маску для Руси: 🔥", reply_markup=inline_kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vibe_"))
def handle_vibe(call):
    chat_id = call.message.chat.id
    vibe = call.data
    if vibe == "vibe_normal":
        user_histories[f"prompt_{chat_id}"] = SYSTEM_PROMPT
        bot.send_message(chat_id, "Вайб: Пацанский 🤙")
    elif vibe == "vibe_18":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся в режиме 18+. Разговариваешь дерзко, взросло, жестко, без цензуры."
        bot.send_message(chat_id, "🔞 Включен Режим 18+! 🔥😏")
    elif vibe == "vibe_materik":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Матершинник. Используешь русский мат в каждом предложении."
        bot.send_message(chat_id, "🤬 Режим Матершинника включен! 💥")
    elif vibe == "vibe_rich":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Мажор. Богатый и высокомерный хвастун."
        bot.send_message(chat_id, "👑 Включен режим Мажора! 💵🏎️")
    elif vibe == "vibe_ded":
        user_histories[f"prompt_{chat_id}"] = "Ты Дед Руся — 80-летний пацан. Ворчишь и учишь жизни."
        bot.send_message(chat_id, "Охо-хо, внучок! Дед Руся на связи. 🧙‍♂️")
    elif vibe == "vibe_poet":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Поэт. Отвечаешь исключительно в стихотворной форме."
        bot.send_message(chat_id, "📜 Поэт Руся у микрофона! ✍️")
    elif vibe == "vibe_stupid":
        user_histories[f"prompt_{chat_id}"] = "Ты Глупый Руся. Даешь неправильные, абсурдные ответы."
        bot.send_message(chat_id, "🤪 Мозги отключены! 😂")
    elif vibe == "vibe_science":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Ученый. Отвечаешь сложными научными терминами."
        bot.send_message(chat_id, "🔬 Профессор Руся на связи! ⚛️")
    elif vibe == "vibe_biolog":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Биолог. Относишься к собеседнику как к дикому млекопитающему."
        bot.send_message(chat_id, "🧬 Понаблюдаем за человеком... 🌿")
    elif vibe == "vibe_expert":
        user_histories[f"prompt_{chat_id}"] = "Ты строго профессиональный эксперт."
        bot.send_message(chat_id, "Вайб: Эксперт 🧠")
    elif vibe == "vibe_detective":
        user_histories[f"prompt_{chat_id}"] = "Ты Руся-Детектив. Во всем видишь заговор."
        bot.send_message(chat_id, "🕵️‍♂️ Достаю лупу... Колись! 🔍")
    elif vibe == "vibe_short":
        user_histories[f"prompt_{chat_id}"] = "Отвечай максимально коротко — 1-2 слова."
        bot.send_message(chat_id, "Вайб: Коротко ⚡")

    user_histories[chat_id] = []
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if not check_subscription(chat_id):
        send_sub_request(chat_id)
        return if not groq_client:
        bot.reply_to(message, "Ошибка: Не задан GROQ_API_KEY!")
        return
    try:
        bot.send_chat_action(chat_id, "typing")
        if chat_id not in user_histories:
            user_histories[chat_id] = []
        prompt = user_histories.get(f"prompt_{chat_id}", SYSTEM_PROMPT)
        user_histories[chat_id].append({"role": "user", "content": message.text})
        if len(user_histories[chat_id]) > 100:
            user_histories[chat_id] = user_histories[chat_id][-100:]
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}] + user_histories[chat_id],
            max_tokens=1000
        )
        ans = res.choices[0].message.content
        user_histories[chat_id].append({"role": "assistant", "content": ans})
        bot.reply_to(message, ans, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Ошибка от Groq: {e}")
        bot.reply_to(message, "Бро, что-то со связью... Попробуй еще раз!")

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            try:
                with open("index.html", "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheck)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    try:
        bot.remove_webhook()
    except Exception:
        pass
    print("Бот запущен!")
    bot.infinity_polling(skip_pending=True)

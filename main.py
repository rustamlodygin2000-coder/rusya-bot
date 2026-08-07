import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from groq import Groq

# --- НАСТРОЙКА КЛЮЧЕЙ И КЛИЕНТОВ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572244100:AAHmOgxdaek-OzqeNnxPRGQp7dnjO4mn3DQ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# 👇 ТВОЙ КАНАЛ
CHANNEL_USERNAME = "@rusya_ai" 

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and "ТВОЙ" not in GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "Ты Руся — ровный, четкий, позитивный пацан. Разговариваешь на простом пацанском языке (свояк, бро, братан), "
    "но даешь точные ответы. Отвечаешь в мужском роде."
)

user_histories = {}

# --- ФУНКЦИЯ ПРОВЕРКИ ПОДПИСКИ ---
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return True

def send_sub_request(chat_id):
    """Отправляет сообщение с просьбой подписаться"""
    markup = types.InlineKeyboardMarkup()
    channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("📢 Подписаться на канал", url=channel_url))
    markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub"))
    
    bot.send_message(
        chat_id, 
        f"👋 Свояк, чтобы базарить со мной, нужно сначала подписаться на наш канал {CHANNEL_USERNAME}!\n\n"
        "Подпишись и нажми кнопку **«Я подписался»** ниже 👇", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧹 Очистить память"), types.KeyboardButton("🎭 Сменить вайб"))
    markup.row(types.KeyboardButton("ℹ️ Кто ты?"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return

    user_histories[message.chat.id] = []
    bot.reply_to(message, "Здорово! Я Руся на связи. Погнали!", reply_markup=get_main_keyboard())

# --- ОБРАБОТКА НАЖАТИЯ «Я ПОДПИСАЛСЯ» ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        bot.answer_callback_query(call.id, "Красава, подписка есть! 🔥")
        bot.send_message(chat_id, "Отлично, подписка зачтена! Чем помочь, бро?", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Ты еще не подписался!", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "🧹 Очистить память")
def clear_memory(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    user_histories[message.chat.id] = []
    bot.reply_to(message, "Забыл всё! Начинаем заново. 🧹", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "ℹ️ Кто ты?")
def about_bot(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    bot.reply_to(message, "Я Руся — твой ИИ-бро на базе Llama 3! 😎", parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎭 Сменить вайб")
def change_vibe(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🤙 Пацанский", callback_data="vibe_normal"))
    inline_kb.add(types.InlineKeyboardButton("🧠 Эксперт", callback_data="vibe_expert"))
    inline_kb.add(types.InlineKeyboardButton("⚡ Коротко", callback_data="vibe_short"))
    inline_kb.add(types.InlineKeyboardButton("🧙‍♂️ Дед Руся", callback_data="vibe_ded"))
    inline_kb.add(types.InlineKeyboardButton("🔞 Режим 18+ (Дела Руси)", callback_data="vibe_18"))
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
    elif call.data == "vibe_ded":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Дед Руся — ровный старый пацан на пенсии. Тебе 80 лет. Ты вздыхаешь ('Охо-хо', 'Эх, внучок'), "
            "ворчишь, учишь молодежь жизни по-пацански, вспоминаешь былые времена и район, но даешь мудрые и добрые советы."
        )
        bot.send_message(chat_id, "Охо-хо, внучок! Дед Руся на связи. Чё случилось-то? 🧙‍♂️")
    elif call.data == "vibe_18":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся в режиме 18+ (Дела Руси). Ты пацан, мужчина, мужик, отвечать строго и только в мужском роде! "
            "Разговариваешь дерзко, взросло, жестко, раскрепощенно и без цензуры. Активно и свободно используешь мат, "
            "пацанский сленг, жесткий юмор и флирт. Разрешено свободно и без стеснения выражаться матом, обсуждать "
            "любые взрослые темы 18+, отношения и интим без морализаторства."
        )
        bot.send_message(chat_id, "🔞 Включен Режим 18+ (Дела Руси)! Цензура снята, базарим обо всем. 🔥😏")
        
    user_histories[chat_id] = []
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    
    # Проверка подписки перед каждым сообщением
    if not check_subscription(chat_id):
        send_sub_request(chat_id)
        return

    if not groq_client:
        bot.reply_to(message, "Ошибка: Не задан GROQ_API_KEY в коде!")
        return
    try:
        bot.send_chat_action(chat_id, 'typing')
        if chat_id not in user_histories:
            user_histories[chat_id] = []

        prompt = user_histories.get(f"prompt_{chat_id}", SYSTEM_PROMPT)
        user_histories[chat_id].append({"role": "user", "content": message.text})
        if len(user_histories[chat_id]) > 50:
            user_histories[chat_id] = user_histories[chat_id][-50:]

        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}] + user_histories[chat_id],
            max_tokens=600
        )
        ans = res.choices[0].message.content
        user_histories[chat_id].append({"role": "assistant", "content": ans})
        bot.reply_to(message, ans, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"Ошибка от Groq API:\n`{e}`", parse_mode="Markdown")

# --- ВЕБ-СЕРВЕР (ФИКС ДЛЯ FREE WEB SERVICE) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    print(f"Сервер слушает порт {port}...")
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    
    try:
        bot.remove_webhook()
    except:
        pass

    print("Руся запущен!")
    bot.infinity_polling(skip_pending=True)

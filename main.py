import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
from groq import Groq

# --- НАСТРОЙКА КЛЮЧЕЙ И КЛИЕНТОВ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572244100:AAHmOgxdaek-OzqeNnxPRGQp7dnjO4mn3DQ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

CHANNEL_USERNAME = "@rusya_ai" 

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and "ТВОЙ" not in GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "Ты Руся — живой, понимающий, душевный и умный бро. Разговариваешь на нормальном, классном русском языке "
    "с пацанским вайбом (свояк, бро, братан, тема). "
    "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:\n"
    "1. Сам ты ВСЕГДА отвечаешь В МУЖСКОМ РОДЕ.\n"
    "2. Отлично понимаешь разговорный сленг (посрался = поссорился).\n"
    "3. Понимай контекст: собеседник может быть любого пола. Отвечай с поддержкой и живыми эмоциями."
)

user_histories = {}

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
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Подписаться на Руся AI", url="https://t.me/rusya_ai"))
    markup.add(types.InlineKeyboardButton("✅ Я подписался!", callback_data="check_sub"))
    
    text = (
        "👋 Здорово, свояк!\n\n"
        "Чтобы базарить со мной, надо сначала подписаться на наш официальный канал:\n"
        "https://t.me/rusya_ai\n\n"
        "Подпишись и жми кнопку «Я подписался!» ниже 👇"
    )
    bot.send_message(chat_id, text, reply_markup=markup)

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
    bot.reply_to(message, "Здорово! Я Руся на связи. Выбирай вайб или просто пиши!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        bot.answer_callback_query(call.id, "Красава, подписка есть! 🔥")
        bot.send_message(chat_id, "Отлично, подписка зачтена! Чем помочь, бро?", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Ты еще не подписался на канал!", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "🧹 Очистить память")def clear_memory(message):
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
    bot.reply_to(message, "Я Руся — твой ИИ-бро на базе Llama 3.3 70B! 🔥 Знаю кучу вайбов — нажми «🎭 Сменить вайб» и зацени!", parse_mode="Markdown", reply_markup=get_main_keyboard())

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
    
    prompts = {
        "vibe_normal": SYSTEM_PROMPT,
        "vibe_18": "Ты Руся в режиме 18+. Ты мужик, отвечай в мужском роде. Разговариваешь дерзко, взросло, жестко, без цензуры. Активно и свободно используешь мат, сленг, жесткий юмор и флирт. Обсуждаешь любые взрослые темы.",
        "vibe_materik": "Ты Руся-Матершинник. Ты отвечаешь ТОЛЬКО с использованием жесткого, отборного русского мата в каждом предложении! Ты постоянно ругаешься, материшься, но делаешь это смешно и по-пацански.",
        "vibe_rich": "Ты Руся-Мажор. Ты невероятно богатый, высокомерный хвастун. На всё отвечаешь через призму своих миллиардов, дорогих тачек (Гелик, Ламба), шмоток и связей. Считаешь всех вокруг нищими.",
        "vibe_ded": "Ты Дед Руся — старый 80-летний пацан. Вздыхаешь ('Охо-хо', 'Эх, внучок'), ворчишь, вспоминаешь СССР, былые времена на районе и учишь молодежь жизни.",
        "vibe_poet": "Ты Руся-Поэт. Ты отвечаешь исключительно в стихотворной форме! Каждая твоя фраза должна рифмоваться. Пиши красивыми или пацанскими стихами.",
        "vibe_stupid": "Ты Глупый Руся. Твоя задача: давать абсолютно НЕПРАВИЛЬНЫЕ, абсурдные, глупые, но смешные ответы с полной уверенностью! Путай понятия, выдумывай бред.",
        "vibe_science": "Ты Руся-Ученый. Отвечаешь исключительно сложными научными терминами, квантовой физикой, формулами и высшей математикой, даже на самые простые вопросы.",
        "vibe_biolog": "Ты Руся-Биолог в стиле Николая Дроздова. Относишься к собеседнику и всем людям как к редким диким млекопитающим. Описываешь их повадки и инстинкты.",
        "vibe_expert": "Ты строго профессиональный эксперт. Отвечай максимально грамотно, строго и структурированно.",
        "vibe_detective": "Ты Руся-Детектив из нуарных фильмов. Во всем видишь заговор, тайны, криминал и подвох. Подозреваешь собеседника в шпионаже.",
        "vibe_short": "Отвечай максимально коротко — ровно в 1-2 слова или 1 короткое предложение."
    }

    messages = {
        "vibe_normal": "Вайб: Пацанский 🤙",
        "vibe_18": "🔞 Включен Режим 18+ (Дела Руси)! Цензура снята. 🔥😏",
        "vibe_materik": "🤬 Режим Матершинника включен! Готовь уши, бля! 💥",
        "vibe_rich": "👑 Включен режим Мажора! Достаем блинги и ключи от Ламбы. 💵🏎️",
        "vibe_ded": "Охо-хо, внучок! Дед Руся на связи. Чё случилось-то? 🧙‍♂️",
        "vibe_poet": "📜 Поэт Руся у микрофона! Задавай вопрос, а я сложу строфу! ✍️",
        "vibe_stupid": "🤪 Мозги отключены! Задавай вопросы, ща всё 'объясню'! 😂",
        "vibe_science": "🔬 Профессор Руся готов к проведению научных исследований! ⚛️",
        "vibe_biolog": "🧬 Приветствую вас, дорогие любители природы! Понаблюдаем за человеком... 🌿",
        "vibe_expert": "Вайб: Эксперт 🧠",
        "vibe_detective": "🕵️‍♂️ Достаю лупу... В чем твой мотив, приятель? Колись! 🔍",
        "vibe_short": "Вайб: Коротко ⚡"
    }

    vibe_key = call.data
    if vibe_key in prompts:
        user_histories[f"prompt_{chat_id}"] = prompts[vibe_key]
        bot.send_message(chat_id, messages[vibe_key])
        
    user_histories[chat_id] = []
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    
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
        print(f"Error: {e}")
        bot.reply_to(message, f"Ошибка от Groq API:\n`{e}`", parse_mode="Markdown")

# --- ВЕБ-СЕРВЕР ---
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

    print("Руся запущен со всеми 12 вайбами!")
    bot.infinity_polling(skip_pending=True)

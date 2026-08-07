from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading
import time
from groq import Groq
import telebot
from telebot import types

# --- НАСТРОЙКА КЛЮЧЕЙ И КЛИЕНТОВ ---
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8572244100:AAHmOgxdaek-OzqeNnxPRGQp7dnjO4mn3DQ"
)
GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY", "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"
)

CHANNEL_USERNAME = "@rusya_ai"
# URL твоего приложения на Render
WEBAPP_URL = "https://rusya-bot.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY and "ТВОЙ" not in GROQ_API_KEY
    else None
)

SYSTEM_PROMPT = (
    "Ты Руся — живой, понимающий, душевный и умный бро. Разговариваешь на нормальном, классном русском языке с пацанским вайбом. "
    "Сам всегда отвечаешь В МУЖСКОМ РОДЕ. Отлично понимаешь сленг и эмоциональный контекст."
)

user_histories = {}
user_balances = {}
daily_rewards = {}


def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return True


def send_sub_request(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📢 Подписаться на Руся AI", url="https://t.me/rusya_ai"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "✅ Я подписался!", callback_data="check_sub"
        )
    )

    text = "👋 Здорово, свояк!\n\nЧтобы базарить со мной, надо сначала подписаться на наш официальный канал:\nhttps://t.me/rusya_ai\n\nПодпишись и жми кнопку «Я подписался!» ниже 👇"
    bot.send_message(chat_id, text, reply_markup=markup)


# --- ГЛАВНАЯ КЛАВИАТУРА МЕНЮ (С КНОПКОЙ MINI APP) ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Кнопка открытия Mini App прямо в Telegram!
    app_button = types.KeyboardButton(
        "📱 Открыть Руся App 🎮", web_app=types.WebAppInfo(url=WEBAPP_URL)
    )

    markup.row(app_button)
    markup.row(
        types.KeyboardButton("🎲 Играть в кости"),
        types.KeyboardButton("🎰 Мой Баланс"),
    )
    markup.row(
        types.KeyboardButton("🎁 Ежедневный бонус"),
        types.KeyboardButton("🏆 Топ Авторитетов"),
    )
    markup.row(
        types.KeyboardButton("🧹 Очистить память"),
        types.KeyboardButton("🎭 Сменить вайб"),
    )
    markup.row(types.KeyboardButton("ℹ️ Кто ты?"))
    return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return

    user_histories[message.chat.id] = []
    bot.reply_to(
        message,
        "Здорово! Я Руся на связи. Заходи в наше Mini App приложение или катай в кости!",
        reply_markup=get_main_keyboard(),
    )


# Прием данных из Mini App при закрытии
@bot.message_handler(content_types=["web_app_data"])
def handle_web_app_data(message):
    chat_id = message.chat.id
    try:
        data = json.loads(message.web_app_data.data)
        if "new_balance" in data:
            user_balances[chat_id] = data["new_balance"]
            bot.reply_to(
                message,
                f"🔥 Красава! Баланс из приложения сохранен! У тебя теперь *{user_balances[chat_id]} Респектов* 🎰",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(),
            )
    except Exception as e:
        print(f"Ошибка приеме данных WebApp: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        bot.answer_callback_query(call.id, "Красава, подписка есть! 🔥")
        bot.send_message(
            chat_id,
            "Отлично, подписка зачтена! Чем помочь, бро?",
            reply_markup=get_main_keyboard(),
        )
    else:
        bot.answer_callback_query(
            call.id, "❌ Ты еще не подписался на канал!", show_alert=True
        )


@bot.message_handler(func=lambda message: message.text == "🧹 Очистить память")
def clear_memory(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    user_histories[message.chat.id] = []
    bot.reply_to(
        message,
        "Забыл всё! Начинаем заново с чистого листа. 🧹",
        reply_markup=get_main_keyboard(),
    )


@bot.message_handler(func=lambda message: message.text == "ℹ️ Кто ты?")
def about_bot(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return
    bot.reply_to(
        message,
        "Я Руся — твой ИИ-бро на базе Llama 3.3 70B! 🔥 Жми «📱 Открыть Руся App 🎮» и фарми Респекты в нашей игре!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )


# --- СМЕНА ВАЙБА ---
@bot.message_handler(func=lambda message: message.text == "🎭 Сменить вайб")
def change_vibe(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return

    inline_kb = types.InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        types.InlineKeyboardButton("🤙 Пацанский", callback_data="vibe_normal"),
        types.InlineKeyboardButton("🔞 Режим 18+", callback_data="vibe_18"),
        types.InlineKeyboardButton(
            "🤬 Матершинник", callback_data="vibe_materik"
        ),
        types.InlineKeyboardButton(
            "👑 Хвастун / Мажор", callback_data="vibe_rich"
        ),
        types.InlineKeyboardButton("🧙‍♂️ Дед Руся", callback_data="vibe_ded"),
        types.InlineKeyboardButton("📜 Поэт", callback_data="vibe_poet"),
        types.InlineKeyboardButton(
            "🤪 Глупый Руся", callback_data="vibe_stupid"
        ),
        types.InlineKeyboardButton("🔬 Ученый", callback_data="vibe_science"),
        types.InlineKeyboardButton("🧬 Биолог", callback_data="vibe_biolog"),
        types.InlineKeyboardButton("🧠 Эксперт", callback_data="vibe_expert"),
        types.InlineKeyboardButton(
            "🕵️‍♂️ Детектив", callback_data="vibe_detective"
        ),
        types.InlineKeyboardButton("⚡ Коротко", callback_data="vibe_short"),
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
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся в режиме 18+. Ты мужик, отвечай в мужском роде. Разговариваешь дерзко, взросло, жестко, без цензуры. Активно и свободно используешь мат, сленг, жесткий юмор и флирт. Обсуждаешь любые взрослые темы."
        )
        bot.send_message(
            chat_id, "🔞 Включен Режим 18+ (Дела Руси)! Цензура снята. 🔥😏"
        )
    elif vibe == "vibe_materik":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Матершинник. Ты отвечаешь ТОЛЬКО с использованием жесткого, отборного русского мата в каждом предложении! Ты постоянно ругаешься, материшься, но делаешь это смешно и по-пацански."
        )
        bot.send_message(
            chat_id, "🤬 Режим Матершинника включен! Готовь уши! 💥"
        )
    elif vibe == "vibe_rich":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Мажор. Ты невероятно богатый, высокомерный хвастун. На всё отвечаешь через призму своих миллиардов, дорогих тачек (Гелик, Ламба), шмоток и связей. Считаешь всех вокруг нищими."
        )
        bot.send_message(
            chat_id,
            "👑 Включен режим Мажора! Достаем блинги и ключи от Ламбы. 💵🏎️",
        )
    elif vibe == "vibe_ded":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Дед Руся — старый 80-летний пацан. Вздыхаешь ('Охо-хо', 'Эх, внучок'), ворчишь, вспоминаешь СССР, былые времена на районе и учишь молодежь жизни."
        )
        bot.send_message(
            chat_id, "Охо-хо, внучок! Дед Руся на связи. Чё случилось-то? 🧙‍♂️"
        )
    elif vibe == "vibe_poet":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Поэт. Ты отвечаешь исключительно в стихотворной форме! Каждая твоя фраза должна рифмоваться. Пиши красивыми или пацанскими стихами."
        )
        bot.send_message(
            chat_id,
            "📜 Поэт Руся у микрофона! Задавай вопрос, а я сложу строфу! ✍️",
        )
    elif vibe == "vibe_stupid":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Глупый Руся. Твоя задача: давать абсолютно НЕПРАВИЛЬНЫЕ, абсурдные, глупые, но смешные ответы с полной уверенностью! Путай понятия, выдумывай бред."
        )
        bot.send_message(
            chat_id, "🤪 Мозги отключены! Задавай вопросы, ща всё 'объясню'! 😂"
        )
    elif vibe == "vibe_science":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Ученый. Отвечаешь исключительно сложными научными терминами, квантовой физикой, формулами и высшей математикой, даже на самые простые вопросы."
        )
        bot.send_message(
            chat_id,
            "🔬 Профессор Руся готов к проведению научных исследований! ⚛️",
        )
    elif vibe == "vibe_biolog":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Биолог в стиле Николая Дроздова. Относишься к собеседнику и всем людям как к редким диким млекопитающим. Описываешь их повадки и инстинкты."
        )
        bot.send_message(
            chat_id,
            "🧬 Приветствую вас, дорогие любители природы! Понаблюдаем за человеком... 🌿",
        )
    elif vibe == "vibe_expert":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты строго профессиональный эксперт. Отвечай максимально грамотно, строго и структурированно."
        )
        bot.send_message(chat_id, "Вайб: Эксперт 🧠")
    elif vibe == "vibe_detective":
        user_histories[f"prompt_{chat_id}"] = (
            "Ты Руся-Детектив из нуарных фильмов. Во всем видишь заговор, тайны, криминал и подвох. Подозреваешь собеседника в шпионаже."
        )
        bot.send_message(
            chat_id,
            "🕵️‍♂️ Достаю лупу... В чем твой мотив, приятель? Колись! 🔍",
        )
    elif vibe == "vibe_short":
        user_histories[f"prompt_{chat_id}"] = (
            "Отвечай максимально коротко — ровно в 1-2 слова или 1 короткое предложение."
        )
        bot.send_message(chat_id, "Вайб: Коротко ⚡")

    user_histories[chat_id] = []
    bot.answer_callback_query(call.id)


# --- ИГРОВАЯ СИСТЕМА ---
@bot.message_handler(func=lambda message: message.text == "🎰 Мой Баланс")
def show_balance(message):
    chat_id = message.chat.id
    if not check_subscription(chat_id):
        send_sub_request(chat_id)
        return

    balance = user_balances.get(chat_id, 100)
    bot.reply_to(
        message,
        f"💳 Твой баланс: *{balance} Респектов* 🎰\n\nФарми их в «📱 Открыть Руся App», играй в кости и забирай ежедневный бонус!",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda message: message.text == "🎁 Ежедневный бонус")
def daily_bonus(message):
    chat_id = message.chat.id
    if not check_subscription(chat_id):send_sub_request(chat_id)
        return

    current_time = time.time()
    last_claim = daily_rewards.get(chat_id, 0)

    if current_time - last_claim >= 86400:
        daily_rewards[chat_id] = current_time
        user_balances[chat_id] = user_balances.get(chat_id, 100) + 50
        bot.reply_to(
            message,
            "🎁 Красава! Держи свои *+50 Респектов*! Приходи завтра за новой порцией.",
            parse_mode="Markdown",
        )
    else:
        time_left = int((86400 - (current_time - last_claim)) // 3600)
        bot.reply_to(
            message,
            f"⏳ Рано еще, свояк! Бонус будет доступен через {time_left} ч.",
        )


@bot.message_handler(func=lambda message: message.text == "🏆 Топ Авторитетов")
def show_top(message):
    if not check_subscription(message.chat.id):
        send_sub_request(message.chat.id)
        return

    if not user_balances:
        bot.reply_to(
            message,
            "Пока никто не играл! Будь первым — жми «📱 Открыть Руся App» или «🎲 Играть в кости»!",
        )
        return

    sorted_users = sorted(
        user_balances.items(), key=lambda x: x[1], reverse=True
    )[:5]

    top_text = "🏆 *ТОП-5 АВТОРИТЕТОВ РАЙОНА:* 🏆\n\n"
    for i, (u_id, bal) in enumerate(sorted_users, 1):
        top_text += f"{i}. Игрок `{u_id}` — *{bal} Респектов*\n"

    bot.reply_to(message, top_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "🎲 Играть в кости")
def play_dice(message):
    chat_id = message.chat.id
    if not check_subscription(chat_id):
        send_sub_request(chat_id)
        return

    balance = user_balances.get(chat_id, 100)
    bet = 50

    if balance < bet:
        bot.reply_to(
            message,
            "❌ Брат, у тебя на балансе пусто! Забери «🎁 Ежедневный бонус» или накликая в «📱 Открыть Руся App».",
        )
        return

    bot.send_message(chat_id, "Твой бросок! 🎲")
    user_dice = bot.send_dice(chat_id)
    user_score = user_dice.dice.value

    time.sleep(2.5)

    bot.send_message(chat_id, "Бросает Руся! 🎲")
    bot_dice = bot.send_dice(chat_id)
    bot_score = bot_dice.dice.value

    time.sleep(2.5)

    if user_score > bot_score:
        user_balances[chat_id] = balance + bet
        res_text = f"🎉 *Ты победил!* ({user_score} против {bot_score})\nЗабираешь *+{bet} Респектов*! Твой баланс: {user_balances[chat_id]}"
    elif user_score < bot_score:
        user_balances[chat_id] = balance - bet
        res_text = f"Увы, Руся забрал победу! 😎 ({bot_score} против {user_score})\nТеряешь *-{bet} Респектов*. Твой баланс: {user_balances[chat_id]}"
    else:
        res_text = f"🤝 *Ничья!* У обоих выпало {user_score}. Респекты остаются при тебе."

    bot.send_message(chat_id, res_text, parse_mode="Markdown")


# --- ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id

    if not check_subscription(chat_id):
        send_sub_request(chat_id)
        return

    if not groq_client:
        bot.reply_to(message, "Ошибка: Не задан GROQ_API_KEY!")
        return

    try:
        bot.send_chat_action(chat_id, "typing")
        if chat_id not in user_histories:
            user_histories[chat_id] = []

        prompt = user_histories.get(f"prompt_{chat_id}", SYSTEM_PROMPT)
        user_histories[chat_id].append(
            {"role": "user", "content": message.text}
        )

        if len(user_histories[chat_id]) > 100:
            user_histories[chat_id] = user_histories[chat_id][-100:]

        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}]
            + user_histories[chat_id],
            max_tokens=1000,
        )
        ans = res.choices[0].message.content
        user_histories[chat_id].append({"role": "assistant", "content": ans})
        bot.reply_to(message, ans, reply_markup=get_main_keyboard())

    except Exception as e:
        print(f"Ошибка от Groq: {e}")
        bot.reply_to(
            message,
            "Бро, что-то со связью... Попробуй еще раз через пару секунд!",
        )


# --- СЕРВЕР ДЛЯ РАЗДАЧИ MINI APP И PING ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        # Если просят главную страницу — отдаем index.html (наш Mini App)
        if self.path == "/" or self.path == "/index.html":
            try:
                with open("index.html", "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error loading index.html: {e}".encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheck)
    print(f"Сервер слушает порт {port}...")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()

    try:
        bot.remove_webhook()
    except Exception:
        pass

    print("Руся AI и Mini App успешно запущены!")
    bot.infinity_polling(skip_pending=True)

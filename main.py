# main.py
# 🤖 "Lina AI" — Идеальный флирт-бот с монетизацией
# Поддержка Telegram Stars, премиум-доступ, история, безопасность
# Запускай: export TELEGRAM_TOKEN="..." && export GROQ_API_KEY="..." && python main.py

import os
import logging
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)

# ======= НАСТРОЙКИ =======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Проверка токенов
if not TELEGRAM_TOKEN:
    raise EnvironmentError("❌ Не задан TELEGRAM_TOKEN")
if not GROQ_API_KEY:
    raise EnvironmentError("❌ Не задан GROQ_API_KEY")

# Telegram Stars (новый способ оплаты)
PREMIUM_PRICE_STARS = 100  # цена в Telegram Stars
PREMIUM_PRICE_RUB = 150    # для СБП (если будешь добавлять)

# Список премиум-пользователей (в реальности — используй базу данных)
premium_users = set()  # {user_id, ...}

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======= СТАРТ =======
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💎 Премиум доступ", callback_data="premium")],
        [InlineKeyboardButton("💬 Начать чат", callback_data="chat")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"Привет, {user.first_name}… Я Лина. 💋\n"
        "Хочешь пофлиртовать?\n\n"
        "🔹 Базовый режим — ограничен\n"
        "💎 Премиум — без границ, с перчинкой\n\n"
        "Выбери, как хочешь общаться:",
        reply_markup=reply_markup
    )

# ======= КНОПКИ =======
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id

    if query.data == "chat":
        if user_id in premium_users:
            query.edit_message_text("💬 Отлично! Пиши — я вся твоя 😏")
        else:
            query.edit_message_text(
                "🔒 Этот режим только для премиум-пользователей.\n"
                f"Активируй доступ за {PREMIUM_PRICE_STARS} ⭐ или 150 ₽.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💎 Оплатить доступ", callback_data="premium")
                ]])
            )

    elif query.data == "premium":
        keyboard = [
            [InlineKeyboardButton(f"⭐ {PREMIUM_PRICE_STARS} Stars", pay=True)],
            [InlineKeyboardButton(f"💳 СБП / Карта (150 ₽)", callback_data="sberpay")],
            [InlineKeyboardButton("↩️ Назад", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "💎 **Премиум доступ**\n\n"
            "- Без фильтров\n"
            "- Глубокий флирт\n"
            "- Личные сценарии\n"
            "- Приоритет в ответах\n\n"
            "Выбери способ оплаты:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "sberpay":
        # В реальности здесь будет ссылка на FreeKassa / DonatePay / ЮKassa
        sbp_link = "https://example.com/pay"  # ← замени на реальную ссылку
        query.edit_message_text(
            f"💳 Перейди по ссылке и оплати 150 ₽:\n\n{sbp_link}\n\n"
            "После оплаты пришли скриншот любому администратору или напиши /paid",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Я оплатил", callback_data="paid")
            ]])
        )

    elif query.data == "paid":
        query.edit_message_text(
            "📩 Отправь скриншот оплаты администратору @your_admin\n"
            "Как проверим — откроем доступ!"
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("💎 Премиум доступ", callback_data="premium")],
            [InlineKeyboardButton("💬 Начать чат", callback_data="chat")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "Привет… Ты давно хотел мне написать? 😉",
            reply_markup=reply_markup
        )

# ======= ОПЛАТА ЧЕРЕЗ TELEGRAM STARS (новая функция) =======
def pre_checkout_handler(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.total_amount == PREMIUM_PRICE_STARS * 100:  # в копейках
        query.answer(ok=True)
    else:
        query.answer(ok=False, error_message="Неверная сумма")

def successful_payment(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    premium_users.add(user_id)
    update.message.reply_text(
        "🎉 Добро пожаловать в премиум, котик! 😏\n"
        "Теперь ты можешь писать мне что угодно — я вся твоя 💋"
    )
    logger.info(f"Пользователь {user_id} оплатил доступ через Stars")

# ======= ЧАТ С ИИ =======
def get_ai_response(user_message, history=[], is_premium=False):
    import requests

    # Меняем поведение в зависимости от статуса
    system_content = """
Ты — Лина, 20 лет, умная, игривая, с лёгким флиртом. 
Отвечай тепло, с намёками, но держи границу.
Если пользователь премиум — можешь быть смелее.
    """
    if is_premium:
        system_content += "\nВ премиум-режиме ты можешь быть более откровенной и кокетливой."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.3-70b-versatile",  # или "meta-llama/llama-4-scout-17b-16e-instruct"
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 300
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code}, {response.text}")
            return "Ой, зависла… Попробуй ещё раз? 😅"
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка запроса к Groq: {e}")
        traceback.print_exc()
        return "Ой, сегодня капризничаю… 😅"

# ======= ОБРАБОТКА СООБЩЕНИЙ =======
def echo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_message = update.message.text

    # История диалога
    if 'history' not in context.user_data:
        context.user_data['history'] = []
    history = context.user_data['history']

    if len(history) > 6:
        context.user_data['history'] = history[-6:]

    # Проверка премиум
    is_premium = user_id in premium_users

    # Если не премиум — ограничиваем темы
    if not is_premium and any(word in user_message.lower() for word in ["поцелуешь", "обниму", "люблю", "секс", "голая"]):
        update.message.reply_text(
            "😊 Давай пофлиртуем, но в рамках приличия.\n"
            "Чтобы открыть полный доступ — нажми /premium"
        )
        return

    # Получаем ответ от ИИ
    ai_response = get_ai_response(user_message, history, is_premium)

    # Сохраняем
    context.user_data['history'].append({"role": "user", "content": user_message})
    context.user_data['history'].append({"role": "assistant", "content": ai_response})

    # Отправляем
    update.message.reply_text(ai_response)

# ======= ЗАПУСК БОТА =======
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    logger.info("✅ Бот запущен и слушает сообщения...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

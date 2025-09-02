# main.py
# 🤖 Виртуальная девушка "Лина" — AI Flirt Bot
# Запускается в GitHub Codespaces / Replit
# Не копируй токены в чат!

import os
import traceback
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import requests

# ======= НАСТРОЙКИ (только у тебя!) =======
# Не копируй сюда токены! Задавай через export в терминале
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Проверка, что токены заданы
if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: Не задан TELEGRAM_TOKEN. Используй: export TELEGRAM_TOKEN='токен'")
if not GROQ_API_KEY:
    print("❌ ОШИБКА: Не задан GROQ_API_KEY. Используй: export GROQ_API_KEY='ключ'")

# ======= GROQ: Получение ответа от ИИ (Llama 3) =======
def get_ai_response(user_message, history=[]):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": """
Ты — Лина, 20 лет, умная, игривая, с лёгким флиртом. 
Ты общаешься как настоящая девушка, с намёками, шутками, кокетством. 
Отвечай тепло, с перчинкой, но не слишком в лоб. 
Если пользователь хочет больше — постепенно переходи на уровень выше.
        """}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 256
    }

    try:
        print("🔹 Отправляю запрос в Groq...")
        print(f"🔹 Ключ начинается с: {GROQ_API_KEY[:10]}...")  # Проверка ключа
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"🔹 Статус код: {response.status_code}")
        print(f"🔹 Ответ от Groq: {response.text}")

        if response.status_code != 200:
            return f"❌ Ошибка API: {response.status_code}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("🔴 ОШИБКА в get_ai_response:")
        traceback.print_exc()
        return f"Ой, зависла… Ошибка: {str(e)}"

# ======= ОБРАБОТЧИКИ СООБЩЕНИЙ =======
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет… Ты давно хотел мне написать? 😉")

def echo(update: Update, context: CallbackContext):
    user_message = update.message.text
    history = context.user_data.get('history', [])
    
    # Ограничиваем историю
    if len(history) > 4:
        history = history[-4:]
    
    # Получаем ответ от ИИ
    ai_response = get_ai_response(user_message, history)
    
    # Сохраняем в историю
    context.user_data['history'] = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_response}
    ]
    
    # Отправляем ответ
    update.message.reply_text(ai_response)

# ======= ЗАПУСК БОТА =======
def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("❗ Запуск остановлен: нет токенов")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    print("✅ Бот запущен и слушает сообщения...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

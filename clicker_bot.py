import time
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id] = {'coins': 0}
    keyboard = [[KeyboardButton("💰 Клик"), KeyboardButton("📊 Профиль")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text('Добро пожаловать в кликер! Нажмите кнопку ниже:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if update.message.text == "💰 Клик":
        await update.message.reply_text("Подождите 2 сек...")
        await asyncio.sleep(2)  # Асинхронное ожидание 2 секунды
        user_data[user_id]['coins'] += 0.5
        await update.message.reply_text("✅ Успешный клик +0.5")
    elif update.message.text == "📊 Профиль":
        coins = user_data[user_id]['coins']
        await update.message.reply_text(f"У вас всего монет: {coins}")

def main():
    application = ApplicationBuilder().token("7528604721:AAHXiumG5pmhg0X-XFrJZK4WK6R0ZtR266Y").build()  # Замените на ваш токен
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button))
    application.run_polling()

if __name__ == '__main__':
    main()

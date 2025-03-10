import logging
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import json

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пути к файлам данных
DATA_FILE = "user_data.json"
BANNED_FILE = "banned_users.json"

# Состояния диалога
AUTH, MAIN_MENU, ADMIN_ACTION = range(3)  # Добавляем новое состояние для админских действий

# Коды доступа
USER_CODE = "User_123"
ADMIN_CODE = "Admin_321"

# Функция для загрузки данных пользователей
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Функция для сохранения данных пользователей
def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Функция для загрузки забаненных пользователей
def load_banned_users():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

# Функция для сохранения забаненных пользователей
def save_banned_users(banned_users):
    with open(BANNED_FILE, "w", encoding="utf-8") as file:
        json.dump(banned_users, file)

# Создание файла со списком пользователей
def create_users_file(user_data):
    with open("users_list.txt", "w", encoding="utf-8") as file:
        file.write("Список пользователей:\n\n")
        for user_id, user_info in user_data.items():
            file.write(f"ID: {user_id}\n")
            file.write(f"Монеты: {user_info['coins']}\n")
            file.write(f"Тип: {'Админ' if user_info.get('is_admin', False) else 'Пользователь'}\n")
            file.write("-" * 30 + "\n")
    return "users_list.txt"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Проверяем, забанен ли пользователь
    user_id = update.effective_user.id
    banned_users = load_banned_users()
    
    if str(user_id) in banned_users:
        await update.message.reply_text("Вы забанены и не можете использовать этого бота.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, введите код доступа для продолжения:"
    )
    return AUTH

# Обработчик ввода кода авторизации
async def authenticate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = load_user_data()
    auth_code = update.message.text
    
    # Проверяем код доступа
    if auth_code == ADMIN_CODE:
        # Админский доступ
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {
                "coins": float('inf'),  # Бесконечное количество монет
                "last_click": 0,
                "is_admin": True
            }
        else:
            user_data[str(user_id)]["is_admin"] = True
            user_data[str(user_id)]["coins"] = float('inf')
        
        save_user_data(user_data)
        
        # Создаем клавиатуру с админскими кнопками
        keyboard = [
            [KeyboardButton("Профиль"), KeyboardButton("КЛИК!")],
            [KeyboardButton("Админ-панель")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Вы авторизованы как администратор!",
            reply_markup=reply_markup
        )
        
    elif auth_code == USER_CODE:
        # Обычный пользователь
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {
                "coins": 0,
                "last_click": 0,
                "is_admin": False
            }
        else:
            user_data[str(user_id)]["is_admin"] = False
        
        save_user_data(user_data)
        
        # Создаем клавиатуру с обычными кнопками
        keyboard = [
            [KeyboardButton("Профиль"), KeyboardButton("КЛИК!")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Вы авторизованы как пользователь!",
            reply_markup=reply_markup
        )
        
    else:
        # Неверный код
        await update.message.reply_text(
            "Неверный код доступа. Пожалуйста, попробуйте снова или введите /start для перезапуска."
        )
        return AUTH
    
    return MAIN_MENU

# Обработчик нажатий на кнопки меню
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = load_user_data()
    text = update.message.text
    
    # Если пользователя нет в данных, отправляем его на авторизацию
    if str(user_id) not in user_data:
        await update.message.reply_text("Необходимо авторизоваться. Введите /start для начала.")
        return ConversationHandler.END
    
    if text == "Профиль":
        # Показываем профиль пользователя
        coins = user_data[str(user_id)]["coins"]
        is_admin = user_data[str(user_id)].get("is_admin", False)
        
        await update.message.reply_text(
            f"Профиль:\nID: {user_id}\nМонеты: {coins if coins != float('inf') else 'Безлимитно'}\n"
            f"Статус: {'Администратор' if is_admin else 'Пользователь'}"
        )
    
    elif text == "КЛИК!":
        current_time = time.time()
        last_click = user_data[str(user_id)]["last_click"]
        
        # Для админа нет задержки
        if user_data[str(user_id)].get("is_admin", False) or current_time - last_click >= 1:
            # Если не админ, добавляем монеты
            if not user_data[str(user_id)].get("is_admin", False):
                user_data[str(user_id)]["coins"] += 0.5
            
            user_data[str(user_id)]["last_click"] = current_time
            save_user_data(user_data)
            
            coins_display = user_data[str(user_id)]["coins"]
            if coins_display == float('inf'):
                coins_display = "Безлимитно"
                
            await update.message.reply_text(
                f"Вы получили 0.5 монет! Теперь у вас {coins_display} монет."
            )
        else:
            # Сообщаем о необходимости подождать
            await update.message.reply_text(
                "Подождите 1 секунду между кликами!"
            )
    
    elif text == "Админ-панель" and user_data[str(user_id)].get("is_admin", False):
        # Показываем админ-панель
        keyboard = [
            [InlineKeyboardButton("Список пользователей", callback_data="list_users")],
            [InlineKeyboardButton("Выдать монеты", callback_data="give_coins")],
            [InlineKeyboardButton("Бан пользователя", callback_data="ban_user")],
            [InlineKeyboardButton("Разбан пользователя", callback_data="unban_user")],
            [InlineKeyboardButton("Вернуться", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Админ-панель. Выберите действие:",
            reply_markup=reply_markup
        )
    
    elif text == "Админ-панель" and not user_data[str(user_id)].get("is_admin", False):
        # Пользователь пытается получить доступ к админке
        await update.message.reply_text(
            "У вас нет прав для доступа к админ-панели."
        )
    
    # Проверяем, находится ли пользователь в режиме админских действий
    elif context.user_data.get("admin_action"):
        # Передаем управление обработчику админских действий
        return await handle_admin_action(update, context)
    
    return MAIN_MENU

# Обработчик callback-запросов от инлайн-кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = load_user_data()
    
    # Проверяем, является ли пользователь админом
    if str(user_id) not in user_data or not user_data[str(user_id)].get("is_admin", False):
        await query.message.edit_text("У вас нет прав для выполнения этого действия.")
        return MAIN_MENU
    
    if query.data == "list_users":
        # Список пользователей
        if len(user_data) > 10:
            # Если больше 10 пользователей, создаем файл
            file_path = create_users_file(user_data)
            await query.message.reply_document(document=open(file_path, "rb"))
            os.remove(file_path)  # Удаляем файл после отправки
        else:
            # Иначе выводим список в сообщении
            users_list = "Список пользователей:\n\n"
            for u_id, u_info in user_data.items():
                users_list += f"ID: {u_id}\n"
                users_list += f"Монеты: {u_info['coins'] if u_info['coins'] != float('inf') else 'Безлимитно'}\n"
                users_list += f"Тип: {'Админ' if u_info.get('is_admin', False) else 'Пользователь'}\n"
                users_list += "-" * 20 + "\n"
            
            await query.message.edit_text(users_list)
        return MAIN_MENU
    
    elif query.data == "give_coins":
        context.user_data["admin_action"] = "give_coins_step1"
        await query.message.edit_text(
            "Введите ID пользователя, которому хотите выдать монеты:"
        )
        return ADMIN_ACTION  # Переход в админское состояние
    
    elif query.data == "ban_user":
        # Предлагаем ввести ID пользователя для бана
        context.user_data["admin_action"] = "ban_user"
        
        await query.message.edit_text(
            "Введите ID пользователя, которого хотите забанить:"
        )
        return ADMIN_ACTION  # Переходим в состояние админских действий
    
    elif query.data == "unban_user":
        # Показываем список забаненных пользователей
        banned_users = load_banned_users()
        
        if not banned_users:
            await query.message.edit_text("Нет забаненных пользователей.")
            return MAIN_MENU
        
        context.user_data["admin_action"] = "unban_user"
        
        banned_list = "Список забаненных пользователей:\n\n"
        for b_id in banned_users:
            banned_list += f"ID: {b_id}\n"
        
        await query.message.edit_text(
            banned_list + "\nВведите ID пользователя, которого хотите разбанить:"
        )
        return ADMIN_ACTION  # Переходим в состояние админских действий
    
    elif query.data == "back":
        # Возвращаемся в основное меню админ-панели
        keyboard = [
            [InlineKeyboardButton("Список пользователей", callback_data="list_users")],
            [InlineKeyboardButton("Выдать монеты", callback_data="give_coins")],
            [InlineKeyboardButton("Бан пользователя", callback_data="ban_user")],
            [InlineKeyboardButton("Разбан пользователя", callback_data="unban_user")],
            [InlineKeyboardButton("Вернуться", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "Админ-панель. Выберите действие:",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    
    return MAIN_MENU

# Обработчик админских действий
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = load_user_data()
    text = update.message.text
    
    # Проверяем, является ли пользователь админом
    if str(user_id) not in user_data or not user_data[str(user_id)].get("is_admin", False):
        await update.message.reply_text("У вас нет прав для выполнения этого действия.")
        return MAIN_MENU
    
    # Получаем текущее действие
    admin_action = context.user_data.get("admin_action", None)
    
    if admin_action == "give_coins_step1":
        # Запоминаем ID пользователя и переходим к следующему шагу
        target_id = text.strip()
        
        if target_id not in user_data:
            await update.message.reply_text("Пользователь с таким ID не найден.")
            # Возвращаемся к обычному меню
            keyboard = [
                [KeyboardButton("Профиль"), KeyboardButton("КЛИК!")],
                [KeyboardButton("Админ-панель")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Операция отменена.", reply_markup=reply_markup)
            context.user_data.pop("admin_action", None)
            return MAIN_MENU
        else:
            context.user_data["target_id"] = target_id
            context.user_data["admin_action"] = "give_coins_step2"
            await update.message.reply_text("Введите количество монет для выдачи:")
            return ADMIN_ACTION
    
    elif admin_action == "give_coins_step2":
        # Выдаем монеты пользователю
        try:
            amount = float(text.strip())
            target_id = context.user_data.get("target_id")
            
            if target_id in user_data:
                # Если у пользователя бесконечное количество монет, то ничего не меняем
                if user_data[target_id]["coins"] != float('inf'):
                    user_data[target_id]["coins"] += amount
                    save_user_data(user_data)
                
                await update.message.reply_text(f"Вы успешно выдали {amount} монет пользователю {target_id}.")
            else:
                await update.message.reply_text("Пользователь с таким ID не найден.")
            
            # Сбрасываем действие
            context.user_data.pop("admin_action", None)
            context.user_data.pop("target_id", None)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное число.")
            return ADMIN_ACTION
    
    elif admin_action == "ban_user":
        # Баним пользователя
        target_id = text.strip()
        banned_users = load_banned_users()
        
        if target_id in banned_users:
            await update.message.reply_text("Этот пользователь уже забанен.")
        else:
            banned_users.append(target_id)
            save_banned_users(banned_users)
            await update.message.reply_text(f"Пользователь {target_id} успешно забанен.")
        
        # Сбрасываем действие
        context.user_data.pop("admin_action", None)
    
    elif admin_action == "unban_user":
        # Разбаниваем пользователя
        target_id = text.strip()
        banned_users = load_banned_users()
        
        if target_id not in banned_users:
            await update.message.reply_text("Этот пользователь не находится в бане.")
        else:
            banned_users.remove(target_id)
            save_banned_users(banned_users)
            await update.message.reply_text(f"Пользователь {target_id} успешно разбанен.")
        
        # Сбрасываем действие
        context.user_data.pop("admin_action", None)
    
    # Показываем админ-панель снова
    keyboard = [
        [InlineKeyboardButton("Список пользователей", callback_data="list_users")],
        [InlineKeyboardButton("Выдать монеты", callback_data="give_coins")],
        [InlineKeyboardButton("Бан пользователя", callback_data="ban_user")],
        [InlineKeyboardButton("Разбан пользователя", callback_data="unban_user")],
        [InlineKeyboardButton("Вернуться", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Админ-панель. Выберите действие:",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

def main() -> None:
    # Создание экземпляра приложения
    application = Application.builder().token("7528604721:AAHXiumG5pmhg0X-XFrJZK4WK6R0ZtR266Y").build()
    
    # Создаем обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, authenticate)],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press),
                CallbackQueryHandler(handle_callback)
            ],
            ADMIN_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_action)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    # Добавляем обработчик диалога
    application.add_handler(conv_handler)
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

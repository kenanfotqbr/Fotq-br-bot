import telebot
from telebot import types
import json
import os
import time
from flask import Flask
import threading

# Веб-сервер для UptimeRobot
app = Flask(__name__)

@app.route('/')
def index():
    return "I'm alive! Bot is working 24/7", 200

@app.route('/status')
def status():
    return {"status": "alive", "message": "Bot is running", "uptime": "OK"}, 200

@app.route('/keep_alive')
def keep_alive():
    return "OK", 200

@app.route('/health')
def health():
    return "healthy", 200

# Инициализация бота
TOKEN = "7339047878:AAELMJ6agFIl3kuKfx0NdJIBgBYCAm_bOVk"
bot = telebot.TeleBot(TOKEN)

OWNER_ID = 5151502625
CHANNEL_USERNAME = '@brquestionshelper'
ADMINS_FILE = 'admins.json'
DATA_FILE = 'data.json'
USERS_FILE = 'users.json'

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_admins():
    with open(ADMINS_FILE, 'w') as f:
        json.dump(ADMINS, f)

ADMINS = load_admins()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            data.setdefault('question_count', 0)
            data.setdefault('pending', {})
            data.setdefault('cooldowns', {})
            data.setdefault('sent_messages', {})
            data.setdefault('history', {})
            data.setdefault('rejected', {})
            return data
    return {
        'question_count': 0,
        'pending': {},
        'cooldowns': {},
        'sent_messages': {},
        'history': {},
        'rejected': {}
    }

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(DATA, f)

DATA = load_data()

# Состояния пользователей
USER_STATES = {}

def set_user_state(user_id, state):
    """Устанавливает состояние пользователя"""
    USER_STATES[user_id] = state

def get_user_state(user_id):
    """Получает состояние пользователя"""
    return USER_STATES.get(user_id, None)

def clear_user_state(user_id):
    """Очищает состояние пользователя"""
    if user_id in USER_STATES:
        del USER_STATES[user_id]

def save_user(user_id):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    else:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

def get_user_count():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        return len(users)
    return 0

def calculate_user_level(user_id):
    """Рассчитывает уровень пользователя на основе активности"""
    user_history = DATA.get('history', {}).get(str(user_id), [])
    
    total_questions = len(user_history)
    answered_questions = len([q for q in user_history if q.get("answer")])
    
    # Очки за активность
    points = total_questions * 10 + answered_questions * 5
    
    # Определение уровня
    if points >= 500:
        return 10, "🏆 Мастер BR", points
    elif points >= 400:
        return 9, "💎 Эксперт", points
    elif points >= 300:
        return 8, "⭐ Профессионал", points
    elif points >= 200:
        return 7, "🔥 Опытный", points
    elif points >= 150:
        return 6, "⚡ Продвинутый", points
    elif points >= 100:
        return 5, "🎯 Активный", points
    elif points >= 70:
        return 4, "📈 Развивающийся", points
    elif points >= 40:
        return 3, "🌟 Участник", points
    elif points >= 20:
        return 2, "🚀 Новичок+", points
    else:
        return 1, "👶 Новичок", points

def get_level_progress(user_id):
    """Показывает прогресс до следующего уровня"""
    level, title, points = calculate_user_level(user_id)
    
    level_thresholds = [0, 20, 40, 70, 100, 150, 200, 300, 400, 500]
    
    if level < 10:
        next_level_points = level_thresholds[level]
        progress = points - (level_thresholds[level-1] if level > 1 else 0)
        needed = next_level_points - (level_thresholds[level-1] if level > 1 else 0)
        return progress, needed
    else:
        return points, points  # Максимальный уровень

def is_subscribed(user_id):
    if user_id == OWNER_ID:
        return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'creator', 'administrator']
    except:
        return False

def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🔍 Найти ответ на свой вопрос')
    btn2 = types.KeyboardButton('👤 Мой кабинет')
    
    if message.from_user.id == OWNER_ID:
        btn3 = types.KeyboardButton('🛠 Админ-панель')
        markup.add(btn1, btn2, btn3)
    elif message.from_user.id in ADMINS:
        btn3 = types.KeyboardButton('📋 Панель админа')
        markup.add(btn1, btn2, btn3)
    else:
        markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "🎮 Добро пожаловать! Здесь ты можешь задать любой вопрос по Black Russia — "
        "от RP-отыгровок до админки, правил сервера и прокачки.\n"
        "📩 Пиши — я отвечу быстро, чётко и по делу.\n"
        "🎯 Помогаю новичкам и опытным игрокам.\n"
        "⚡️ Актуальная инфа, проверенные ответы, без воды.\n\n"
        "Новости: @brquestionshelper"
    )

    user_id = message.from_user.id
    save_user(user_id)
    
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("✅ Подписаться", url="https://t.me/brquestionshelper")
        markup.add(btn)
        text = "👋 Чтобы пользоваться ботом, подпишись на канал!"
        bot.send_message(user_id, text, reply_markup=markup)
        return
    
    bot.send_message(message.chat.id, welcome_text)
    send_main_menu(message)

@bot.message_handler(func=lambda message: message.text == '🔍 Найти ответ на свой вопрос')
def handle_button(message):
    # Устанавливаем состояние, что пользователь готов задать вопрос
    set_user_state(message.from_user.id, "asking_question")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Отмена", callback_data="cancel_question"))
    
    text = (
        "🎮 Привет! Если хотите узнать ответ на свой вопрос, то напишите его конкретно!\n\n"
        "Пример:\n"
        "1. Ваш Ник\n"
        "2. Ваш Вопрос\n\n"
        "Ответ на ваш вопрос будет опубликован в Боте❗️")
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '👤 Мой кабинет')
def handle_cabinet(message):
    show_user_history(message.chat.id, page=1, filter_type="all")

@bot.message_handler(func=lambda message: message.text == '🛠 Админ-панель')
def handle_owner_panel(message):
    if message.from_user.id != OWNER_ID:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("👥 Управление админами", callback_data="manage_admins"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="owner_stats")
    )
    markup.row(
        types.InlineKeyboardButton("📝 Все вопросы", callback_data="all_questions"),
        types.InlineKeyboardButton("✉️ Рассылка", callback_data="broadcast")
    )
    
    bot.send_message(message.chat.id, "🛠 Админ-панель владельца:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📋 Панель админа')
def handle_admin_panel(message):
    if message.from_user.id not in ADMINS:
        return
    
    pending_count = len(DATA.get('pending', {}))
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"⏳ Ожидающие вопросы ({pending_count})", callback_data="pending_questions")
    )
    
    bot.send_message(message.chat.id, "📋 Панель администратора:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "manage_admins")
def handle_manage_admins(call):
    if call.from_user.id != OWNER_ID:
        return
    
    admin_list = "\n".join([f"• {admin_id}" for admin_id in ADMINS]) if ADMINS else "Нет администраторов"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ Удалить админа", callback_data="remove_admin")
    )
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_owner"))
    
    bot.edit_message_text(
        f"👥 Список администраторов:\n\n{admin_list}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "owner_stats")
def handle_owner_stats(call):
    if call.from_user.id != OWNER_ID:
        return
    
    user_count = get_user_count()
    pending_count = len(DATA.get('pending', {}))
    total_questions = DATA.get('question_count', 0)
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_owner"))
    
    bot.edit_message_text(
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {user_count}\n"
        f"❓ Всего вопросов: {total_questions}\n"
        f"⏳ Ожидающих ответа: {pending_count}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "all_questions")
def handle_all_questions(call):
    if call.from_user.id != OWNER_ID:
        return
    
    show_all_questions(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "pending_questions")
def handle_pending_questions(call):
    if call.from_user.id not in ADMINS:
        return
    
    pending = DATA.get('pending', {})
    if not pending:
        bot.answer_callback_query(call.id, "Нет ожидающих вопросов")
        return
    
    text = "⏳ Ожидающие вопросы:\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for q_id, user_id in list(pending.items())[:5]:  # Показываем первые 5
        user_history = DATA.get('history', {}).get(str(user_id), [])
        question = next((q for q in reversed(user_history) if q.get('id') == q_id), {})
        question_text = question.get('question', 'Неизвестный вопрос')[:30] + "..."
        
        markup.row(types.InlineKeyboardButton(
            f"❓ {q_id}: {question_text}",
            callback_data=f"view_question_{q_id}"
        ))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_question_"))
def handle_view_question(call):
    if call.from_user.id not in ADMINS:
        return
    
    question_id = call.data.split("_")[2]
    user_id = DATA.get('pending', {}).get(question_id)
    
    if not user_id:
        bot.answer_callback_query(call.id, "Вопрос не найден")
        return
    
    user_history = DATA.get('history', {}).get(str(user_id), [])
    question = next((q for q in reversed(user_history) if q.get('id') == question_id), {})
    
    if not question:
        bot.answer_callback_query(call.id, "Вопрос не найден")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Ответить", callback_data=f"reply_{question_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{question_id}")
    )
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="pending_questions"))
    
    bot.edit_message_text(
        f"❓ Вопрос №{question_id}\n"
        f"👤 От пользователя ID: {user_id}\n\n"
        f"📝 Вопрос:\n{question.get('question', 'Неизвестный вопрос')}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def handle_reject_question(call):
    if call.from_user.id not in ADMINS:
        return
    
    question_id = call.data.split("_")[1]
    set_user_state(call.from_user.id, f"rejecting_{question_id}")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, f"Введите причину отклонения вопроса №{question_id}:")
    bot.register_next_step_handler(call.message, process_rejection, question_id, call.from_user.full_name)

def process_rejection(message, question_id, admin_name):
    if message.from_user.id not in ADMINS:
        return
    
    clear_user_state(message.from_user.id)
    
    if question_id not in DATA['pending']:
        bot.send_message(message.chat.id, "Вопрос уже обработан.")
        return
    
    reason = message.text
    user_id = DATA['pending'].pop(question_id)
    
    # Сохраняем отклоненный вопрос
    DATA['rejected'][question_id] = {
        'user_id': user_id,
        'reason': reason,
        'admin': admin_name
    }
    
    # Обновляем историю пользователя
    user_history = DATA['history'].get(str(user_id), [])
    for entry in reversed(user_history):
        if entry.get('id') == question_id:
            entry['rejected'] = True
            entry['rejection_reason'] = reason
            break
    
    save_data()
    
    # Уведомляем пользователя
    try:
        bot.send_message(
            user_id,
            f"❌ Ваш вопрос №{question_id} был отклонен.\n\n"
            f"📝 Причина: {reason}\n\n"
            f"Попробуйте переформулировать вопрос или задать другой."
        )
    except:
        pass
    
    bot.send_message(message.chat.id, f"✅ Вопрос №{question_id} отклонен.")
    
    # Удаляем сообщения у других админов
    for admin_id in ADMINS:
        try:
            msg_id = DATA['sent_messages'].get(question_id)
            if msg_id:
                bot.edit_message_text(
                    f"❌ Вопрос №{question_id} был отклонен админом {admin_name}.\n"
                    f"Причина: {reason}",
                    chat_id=admin_id,
                    message_id=msg_id
                )
        except:
            pass
    
    if question_id in DATA['sent_messages']:
        del DATA['sent_messages'][question_id]
    
    save_data()

def show_all_questions(chat_id, message_id, page=1):
    all_questions = []
    
    for user_id, history in DATA.get('history', {}).items():
        for entry in history:
            all_questions.append({
                'user_id': user_id,
                'question_id': entry.get('id'),
                'question': entry.get('question'),
                'answer': entry.get('answer'),
                'rejected': entry.get('rejected', False),
                'rejection_reason': entry.get('rejection_reason')
            })
    
    all_questions.sort(key=lambda x: int(x['question_id']), reverse=True)
    
    if not all_questions:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_owner"))
        bot.edit_message_text("Нет вопросов", chat_id, message_id, reply_markup=markup)
        return
    
    per_page = 5
    total_pages = (len(all_questions) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    
    text = f"📝 Все вопросы (страница {page}/{total_pages}):\n\n"
    
    markup = types.InlineKeyboardMarkup()
    
    for q in all_questions[start:end]:
        status = "❌ Отклонен" if q['rejected'] else ("✅ Отвечен" if q['answer'] else "⏳ Ожидает")
        text += f"{status} №{q['question_id']} от ID {q['user_id']}\n"
        text += f"❓ Вопрос: {q['question']}\n"
        
        # Показываем ответ если есть
        if q['answer']:
            text += f"💬 Ответ: {q['answer']}\n"
        elif q['rejected']:
            text += f"🚫 Причина отклонения: {q.get('rejection_reason', 'Не указана')}\n"
        
        # Добавляем кнопки для ответа и отклонения неотвеченных вопросов
        if not q['answer'] and not q['rejected']:
            markup.row(
                types.InlineKeyboardButton(
                    f"💬 Ответить на №{q['question_id']}", 
                    callback_data=f"owner_reply_{q['question_id']}"
                ),
                types.InlineKeyboardButton(
                    f"❌ Отклонить №{q['question_id']}", 
                    callback_data=f"owner_reject_{q['question_id']}"
                )
            )
        text += "\n"
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"all_q_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"all_q_page_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_owner"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("all_q_page_"))
def handle_all_questions_page(call):
    if call.from_user.id != OWNER_ID:
        return
    
    page = int(call.data.split("_")[3])
    show_all_questions(call.message.chat.id, call.message.message_id, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith("owner_reply_"))
def handle_owner_reply(call):
    if call.from_user.id != OWNER_ID:
        return
    
    question_id = call.data.split("_")[2]
    
    # Находим пользователя по вопросу
    user_id = None
    for uid, history in DATA.get('history', {}).items():
        for entry in history:
            if entry.get('id') == question_id and not entry.get('answer') and not entry.get('rejected'):
                user_id = int(uid)
                break
        if user_id:
            break
    
    if not user_id:
        bot.answer_callback_query(call.id, "Вопрос не найден или уже обработан")
        return
    
    set_user_state(call.from_user.id, f"owner_replying_{question_id}")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, f"📝 Введите ответ на вопрос №{question_id}:")
    bot.register_next_step_handler(call.message, process_owner_reply, question_id, user_id)

def process_owner_reply(message, question_id, user_id):
    if message.from_user.id != OWNER_ID:
        return
    
    clear_user_state(message.from_user.id)

    answer_text = message.text
    try:
        # Удаляем из pending если есть
        if question_id in DATA.get('pending', {}):
            del DATA['pending'][question_id]
        
        # Обновляем историю
        history = DATA['history'].get(str(user_id), [])
        question_text = None
        for entry in reversed(history):
            if entry['id'] == question_id:
                entry['answer'] = answer_text
                question_text = entry.get("question", "Ваш вопрос")
                break

        if question_text:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔎 Проверить ответ на свой вопрос", callback_data=f"getanswer_{question_id}"))
            bot.send_message(user_id, f"📨 Твой вопрос:\n\n{question_text}", reply_markup=markup)
            bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю.")
        
        save_data()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при отправке ответа: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("owner_reject_"))
def handle_owner_reject(call):
    if call.from_user.id != OWNER_ID:
        return
    
    question_id = call.data.split("_")[2]
    
    # Находим пользователя по вопросу
    user_id = None
    for uid, history in DATA.get('history', {}).items():
        for entry in history:
            if entry.get('id') == question_id and not entry.get('answer') and not entry.get('rejected'):
                user_id = int(uid)
                break
        if user_id:
            break
    
    if not user_id:
        bot.answer_callback_query(call.id, "Вопрос не найден или уже обработан")
        return
    
    set_user_state(call.from_user.id, f"owner_rejecting_{question_id}")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, f"📝 Введите причину отклонения вопроса №{question_id}:")
    bot.register_next_step_handler(call.message, process_owner_rejection, question_id, user_id)

def process_owner_rejection(message, question_id, user_id):
    if message.from_user.id != OWNER_ID:
        return
    
    clear_user_state(message.from_user.id)

    reason = message.text
    try:
        # Удаляем из pending если есть
        if question_id in DATA.get('pending', {}):
            del DATA['pending'][question_id]
        
        # Сохраняем отклоненный вопрос
        DATA['rejected'][question_id] = {
            'user_id': user_id,
            'reason': reason,
            'admin': 'Владелец'
        }
        
        # Обновляем историю пользователя
        history = DATA['history'].get(str(user_id), [])
        for entry in reversed(history):
            if entry.get('id') == question_id:
                entry['rejected'] = True
                entry['rejection_reason'] = reason
                break
        
        save_data()
        
        # Уведомляем пользователя
        try:
            bot.send_message(
                user_id,
                f"❌ Ваш вопрос №{question_id} был отклонен.\n\n"
                f"📝 Причина: {reason}\n\n"
                f"Попробуйте переформулировать вопрос или задать другой."
            )
        except:
            pass
        
        bot.send_message(message.chat.id, f"✅ Вопрос №{question_id} отклонен.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при отклонении вопроса: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "add_admin")
def handle_add_admin(call):
    if call.from_user.id != OWNER_ID:
        return
    
    set_user_state(call.from_user.id, "adding_admin")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "Введите ID пользователя для добавления в админы:")
    bot.register_next_step_handler(call.message, process_add_admin)

def process_add_admin(message):
    if message.from_user.id != OWNER_ID:
        return
    
    clear_user_state(message.from_user.id)
    
    try:
        admin_id = int(message.text)
        if admin_id not in ADMINS:
            ADMINS.append(admin_id)
            save_admins()
            bot.send_message(message.chat.id, f"✅ Админ добавлен: ID {admin_id}")
            try:
                bot.send_message(admin_id, "🎉 Вам выданы права администратора!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ Этот пользователь уже админ.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID. Введите число.")

@bot.callback_query_handler(func=lambda call: call.data == "remove_admin")
def handle_remove_admin(call):
    if call.from_user.id != OWNER_ID:
        return
    
    set_user_state(call.from_user.id, "removing_admin")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "Введите ID админа для удаления:")
    bot.register_next_step_handler(call.message, process_remove_admin)

def process_remove_admin(message):
    if message.from_user.id != OWNER_ID:
        return
    
    clear_user_state(message.from_user.id)
    
    try:
        admin_id = int(message.text)
        if admin_id in ADMINS:
            ADMINS.remove(admin_id)
            save_admins()
            bot.send_message(message.chat.id, f"✅ Админ удален: ID {admin_id}")
            try:
                bot.send_message(admin_id, "❌ С вас сняты права администратора.")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ Этот пользователь не является админом.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID. Введите число.")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def handle_broadcast_callback(call):
    if call.from_user.id != OWNER_ID:
        return
    
    set_user_state(call.from_user.id, "waiting_broadcast")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Отмена", callback_data="cancel_broadcast"))
    
    bot.edit_message_text(
        "✉️ Введите текст рассылки:\n\n(Поддерживается HTML форматирование: <b>жирный</b>, <i>курсив</i>, <u>подчеркнутый</u>)",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )
    bot.register_next_step_handler(call.message, send_broadcast)

def send_broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    
    clear_user_state(message.from_user.id)
    
    text = message.text
    sent = 0
    failed = 0

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    else:
        users = []

    for user_id in users:
        try:
            # Отправляем с поддержкой HTML форматирования
            bot.send_message(user_id, text, parse_mode='HTML')
            sent += 1
        except:
            failed += 1

    bot.send_message(message.chat.id, f"✅ Рассылка завершена!\nОтправлено: {sent}\nНе удалось: {failed}")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def handle_cancel_broadcast(call):
    if call.from_user.id != OWNER_ID:
        return
    
    clear_user_state(call.from_user.id)
    bot.answer_callback_query(call.id, "Рассылка отменена")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("👥 Управление админами", callback_data="manage_admins"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="owner_stats")
    )
    markup.row(
        types.InlineKeyboardButton("📝 Все вопросы", callback_data="all_questions"),
        types.InlineKeyboardButton("✉️ Рассылка", callback_data="broadcast")
    )
    
    bot.edit_message_text("🛠 Админ-панель владельца:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_question")
def handle_cancel_question(call):
    clear_user_state(call.from_user.id)
    bot.answer_callback_query(call.id, "Отменено")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_main_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_owner")
def handle_back_to_owner(call):
    if call.from_user.id != OWNER_ID:
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("👥 Управление админами", callback_data="manage_admins"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="owner_stats")
    )
    markup.row(
        types.InlineKeyboardButton("📝 Все вопросы", callback_data="all_questions"),
        types.InlineKeyboardButton("✉️ Рассылка", callback_data="broadcast")
    )
    
    bot.edit_message_text("🛠 Админ-панель владельца:", call.message.chat.id, call.message.message_id, reply_markup=markup)

def show_user_history(chat_id, page=1, filter_type="all"):
    user_id = str(chat_id)
    all_history = DATA.get('history', {}).get(user_id, [])

    # Получаем информацию об уровне
    level, title, points = calculate_user_level(chat_id)
    progress, needed = get_level_progress(chat_id)
    
    # Статистика
    total_questions = len(all_history)
    answered_questions = len([q for q in all_history if q.get("answer")])
    rejected_questions = len([q for q in all_history if q.get("rejected")])
    
    # Прогресс-бар
    if level < 10:
        progress_bar = "▓" * (progress * 10 // needed) + "░" * (10 - (progress * 10 // needed))
        level_info = f"🎮 Мой кабинет\n\n" \
                    f"👤 Уровень: {level} {title}\n" \
                    f"⭐ Очки: {points}\n" \
                    f"📊 Прогресс: {progress}/{needed}\n" \
                    f"[{progress_bar}]\n\n" \
                    f"📈 Статистика:\n" \
                    f"❓ Вопросов задано: {total_questions}\n" \
                    f"✅ Ответов получено: {answered_questions}\n" \
                    f"❌ Отклонено: {rejected_questions}\n\n"
    else:
        level_info = f"🎮 Мой кабинет\n\n" \
                    f"👤 Уровень: {level} {title}\n" \
                    f"⭐ Очки: {points}\n" \
                    f"🏆 МАКСИМАЛЬНЫЙ УРОВЕНЬ!\n\n" \
                    f"📈 Статистика:\n" \
                    f"❓ Вопросов задано: {total_questions}\n" \
                    f"✅ Ответов получено: {answered_questions}\n" \
                    f"❌ Отклонено: {rejected_questions}\n\n"

    if filter_type == "answered":
        history = [q for q in all_history if q.get("answer")]
    elif filter_type == "unanswered":
        history = [q for q in all_history if not q.get("answer") and not q.get("rejected")]
    elif filter_type == "rejected":
        history = [q for q in all_history if q.get("rejected")]
    else:
        history = all_history

    if not history:
        text = level_info + "Нет данных по выбранному фильтру."
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📄 Все", callback_data="filter_all"),
            types.InlineKeyboardButton("✅ С ответом", callback_data="filter_answered"))
        markup.row(
            types.InlineKeyboardButton("✉️ Без ответа", callback_data="filter_unanswered"),
            types.InlineKeyboardButton("❌ Отклоненные", callback_data="filter_rejected"))
        bot.send_message(chat_id, text, reply_markup=markup)
        return

    per_page = 3
    total_pages = (len(history) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page

    text = level_info + f"📋 Твои вопросы ({filter_type}) — страница {page}/{total_pages}:\n\n"
    for i, pair in enumerate(history[start:end], start=start + 1):
        question = pair.get("question", "—")
        if pair.get("rejected"):
            status = "❌"
        elif pair.get("answer"):
            status = "✅"
        else:
            status = "⏳"
        text += f"{status} {i}. {question}\n"
        
        # Показываем ответ если есть
        if pair.get("answer"):
            text += f"💬 Ответ: {pair['answer']}\n"
        elif pair.get("rejected"):
            text += f"🚫 Причина отклонения: {pair.get('rejection_reason', 'Не указана')}\n"
        text += "\n"

    markup = types.InlineKeyboardMarkup()
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_{filter_type}"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("➡️ Вперёд", callback_data=f"page_{page+1}_{filter_type}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)

    markup.row(
        types.InlineKeyboardButton("📄 Все", callback_data="filter_all"),
        types.InlineKeyboardButton("✅ С ответом", callback_data="filter_answered"))
    markup.row(
        types.InlineKeyboardButton("✉️ Без ответа", callback_data="filter_unanswered"),
        types.InlineKeyboardButton("❌ Отклоненные", callback_data="filter_rejected"))

    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_page_callback(call):
    parts = call.data.split('_')
    page = int(parts[1])
    filter_type = parts[2]
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_user_history(call.message.chat.id, page=page, filter_type=filter_type)

@bot.callback_query_handler(func=lambda call: call.data.startswith('filter_'))
def handle_filter_callback(call):
    filter_type = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_user_history(call.message.chat.id, page=1, filter_type=filter_type)

@bot.message_handler(func=lambda message: True)
def forward_to_admins(message):
    user = message.from_user
    user_id = user.id
    question_text = message.text
    username = user.username or 'без_ника'

    # Проверяем состояние пользователя
    user_state = get_user_state(user_id)
    if user_state and user_state != "asking_question":
        # Пользователь находится в процессе ввода данных для админских функций
        # Не обрабатываем как обычный вопрос
        return

    # Проверяем подписку
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("✅ Подписаться", url="https://t.me/brquestionshelper")
        markup.add(btn)
        bot.send_message(user_id, "👋 Чтобы пользоваться ботом, подпишись на канал!", reply_markup=markup)
        return

    # Игнорируем команды и кнопки
    if message.text.startswith('/') or message.text in ['🔍 Найти ответ на свой вопрос', '👤 Мой кабинет', '🛠 Админ-панель', '📋 Панель админа']:
        return
    
    # Если пользователь не в состоянии "asking_question", игнорируем сообщение
    if user_state != "asking_question":
        return
    
    # Очищаем состояние после получения вопроса
    clear_user_state(user_id)

    now = int(time.time())
    last_time = DATA['cooldowns'].get(str(user_id), 0)
    if now - last_time < 60:
        bot.send_message(user_id, "Подожди 1 минуту перед следующим вопросом.")
        return

    DATA['cooldowns'][str(user_id)] = now
    DATA['question_count'] += 1
    question_id = str(DATA['question_count'])
    DATA['pending'][question_id] = user_id

    if str(user_id) not in DATA['history']:
        DATA['history'][str(user_id)] = []

    DATA['history'][str(user_id)].append({
        "id": question_id,
        "question": question_text,
        "answer": None,
        "rejected": False
    })

    save_data()

    # Отправляем админам
    for admin_id in ADMINS:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ Ответить", callback_data=f"reply_{question_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{question_id}")
            )
            msg = bot.send_message(
                admin_id,
                f"❓ Новый вопрос №{question_id}\n"
                f"👤 От @{username} (ID: {user_id}):\n\n"
                f"📝 {question_text}",
                reply_markup=markup)
            DATA['sent_messages'][question_id] = msg.message_id
        except:
            pass

    save_data()
    bot.send_message(user_id, "✅ Вопрос отправлен! Ожидай ответ.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def handle_reply_callback(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "У тебя нет прав отвечать.")
        return

    question_id = call.data.split('_')[1]
    if question_id not in DATA['pending']:
        bot.answer_callback_query(call.id, "Этот вопрос уже получил ответ.")
        return

    user_id = DATA['pending'].pop(question_id)
    save_data()

    set_user_state(call.from_user.id, f"replying_{question_id}")
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, f"📝 Введи ответ на вопрос №{question_id}:")
    bot.register_next_step_handler(call.message, process_admin_reply, question_id, user_id, call.from_user.full_name)

def process_admin_reply(message, question_id, user_id, admin_name):
    if message.from_user.id not in ADMINS:
        return
    
    clear_user_state(message.from_user.id)

    answer_text = message.text
    try:
        history = DATA['history'].get(str(user_id), [])
        for entry in reversed(history):
            if entry['id'] == question_id:
                entry['answer'] = answer_text
                break

        question_text = entry.get("question", "Ваш вопрос")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔎 Проверить ответ на свой вопрос", callback_data=f"getanswer_{question_id}"))
        bot.send_message(user_id, f"📨 Твой вопрос:\n\n{question_text}", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Ответ отправлен.")

        # Обновляем сообщения у других админов
        for admin_id in ADMINS:
            try:
                msg_id = DATA['sent_messages'].get(question_id)
                if msg_id:
                    bot.edit_message_text(
                        f"✅ Вопрос №{question_id} был обработан админом {admin_name}.",
                        chat_id=admin_id,
                        message_id=msg_id
                    )
            except:
                pass

        if question_id in DATA['sent_messages']:
            del DATA['sent_messages'][question_id]

        save_data()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при отправке ответа: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("getanswer_"))
def handle_get_answer(call):
    user_id = str(call.from_user.id)
    question_id = call.data.split("_")[1]

    history = DATA['history'].get(user_id, [])
    found = None

    for entry in history:
        if entry.get("id") == question_id:
            found = entry
            break

    if found:
        if found.get("rejected"):
            reason = found.get("rejection_reason", "Не указана")
            bot.answer_callback_query(call.id)
            bot.send_message(call.from_user.id, f"❌ Ваш вопрос №{question_id} был отклонен.\n\n📝 Причина: {reason}")
        elif found.get("answer"):
            bot.answer_callback_query(call.id)
            bot.send_message(call.from_user.id, f"📬 Ответ на твой вопрос №{question_id}:\n\n{found['answer']}")
        else:
            bot.answer_callback_query(call.id, "Ответ пока не готов.")
    else:
        bot.answer_callback_query(call.id, "Вопрос не найден.")

def run_web():
    """Запуск веб-сервера для UptimeRobot"""
    port = int(os.environ.get('PORT', 5000))
    while True:
        try:
            print(f"🌐 Веб-сервер запущен на порту {port}")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ Ошибка веб-сервера: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    # Даем время веб-серверу запуститься
    time.sleep(2)
    
    print("🤖 Telegram бот запускается...")
    print("✅ Веб-сервер работает для UptimeRobot на порту 5000")
    
    # Запускаем бота с обработкой ошибок
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка бота: {e}")
            print("🔄 Перезапуск через 15 секунд...")
            time.sleep(15)

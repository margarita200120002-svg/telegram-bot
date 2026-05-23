from telebot import types
import telebot
import random
import threading
import time

bot = telebot.TeleBot('8535997587:AAEawSleCph_5T7xVCFKaXRqmWeAXuWKEEU')

# =========================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
# =========================
users = {}

# =========================
# РАНДОМНЫЕ ФРАЗЫ
# =========================
correct_answers = [
    '✅ Верно!',
    '✅ Пойдет!',
    '✅ Неплохо!',
    '✅ Слишком просто!',
    '✅ Повезло!',
    '✅ Хоть где-то ты прав.',
]

wrong_answers = [
    '❌ Ну кто бы сомневался',
    '❌ ...',
    '❌ Упс, неверно',
    '❌ Не разочаровывай меня',
    '🤡 Соберись',
    '❌ Опять неправильно',
]

slow_messages = [
    '💤 Долго думаешь...',
    '💤 Мееедленно',
    '💤 Время идёт...',
    '💤 Быстрее!',
]

# =========================
# СОЗДАНИЕ ПРИМЕРОВ
# =========================
def create_examples():

    examples = []

    # Умножение на 1.5
    for number in range(5, 105, 5):

        examples.append({
            'question': f'{number} × 1.5',
            'answer': number * 1.5
        })

    # Таблица AR
    for i in range(2, 20):

        examples.append({
            'question': f'{i} × 5',
            'answer': i * 5
        })

        examples.append({
            'question': f'{i} × 8',
            'answer': i * 8
        })

        examples.append({
            'question': f'{i} × 11',
            'answer': i * 11
        })

        examples.append({
            'question': f'{i} × 17',
            'answer': i * 17
        })

        examples.append({
            'question': f'{i} × 35',
            'answer': i * 35
        })

        examples.append({
            'question': f'{i} × 25',
            'answer': i * 25
        })

    random.shuffle(examples)

    return examples

# =========================
# МЕНЮ
# =========================
def main_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    start_btn = types.InlineKeyboardButton(
        '🚀 Начать',
        callback_data='start_game'
    )

    stats_btn = types.InlineKeyboardButton(
        '📊 Статистика',
        callback_data='stats'
    )

    stop_btn = types.InlineKeyboardButton(
        '⛔ Закончить',
        callback_data='stop_game'
    )

    markup.add(start_btn)
    markup.add(stats_btn, stop_btn)

    return markup

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    users[message.chat.id] = {
        'examples': create_examples(),
        'current': 0,
        'correct': 0,
        'wrong': 0,
        'active': False,
        'question_id': 0,
        'start_time': 0,
        'total_response_time': 0,
        'question_start_time': 0
    }

    bot.send_message(
        message.chat.id,
        '🧠 <b>Удачи, гений</b>\n\n'
        '⏰ На каждый пример даётся 10 секунд.\n'
        'Если долго думаешь — бот напомнит 😈',
        parse_mode='HTML',
        reply_markup=main_menu()
    )

# =========================
# КНОПКА НАЧАТЬ
# =========================
@bot.callback_query_handler(func=lambda call: call.data == 'start_game')
def start_game(call):

    user = users.get(call.message.chat.id)

    if not user:
        return

    user['active'] = True
    user['start_time'] = time.time()

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        '🚀 Начали!'
    )

    send_question(call.message.chat.id)

# =========================
# КНОПКА СТОП
# =========================
@bot.callback_query_handler(func=lambda call: call.data == 'stop_game')
def stop_game(call):

    if call.message.chat.id not in users:
        return

    show_stats(call.message.chat.id)

    users[call.message.chat.id]['active'] = False

    bot.answer_callback_query(call.id)

# =========================
# КНОПКА СТАТИСТИКА
# =========================
@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def stats_button(call):

    if call.message.chat.id not in users:
        return

    show_stats(call.message.chat.id)

    bot.answer_callback_query(call.id)

# =========================
# ПОКАЗ СТАТИСТИКИ
# =========================
def show_stats(chat_id):

    user = users[chat_id]

    total = user['correct'] + user['wrong']

    percent = 0

    if total > 0:
        percent = round(user['correct'] / total * 100)

    # время сессии
    session_time = round(time.time() - user['start_time'])

    minutes = session_time // 60
    seconds = session_time % 60

    # среднее время ответа
    average_time = 0

    if total > 0:
        average_time = round(
            user['total_response_time'] / total,
            2
        )

    stats = (
        '📈 <b>Статистика</b>\n\n'
        f'✅ Правильных: {user["correct"]}\n'
        f'❌ Ошибок: {user["wrong"]}\n'
        f'📊 Процент: {percent}%\n\n'
        f'⏳ Время сессии: {minutes} мин {seconds} сек\n'
        f'⚡ Среднее время ответа: {average_time} сек'
    )

    bot.send_message(
        chat_id,
        stats,
        parse_mode='HTML'
    )

# =========================
# ОТПРАВКА ВОПРОСА
# =========================
def send_question(chat_id):

    user = users[chat_id]

    if not user['active']:
        return

    # закончились примеры
    if user['current'] >= len(user['examples']):

        bot.send_message(
            chat_id,
            '🏁 Все примеры решены!'
        )

        show_stats(chat_id)

        user['active'] = False

        return

    example = user['examples'][user['current']]

    user['question_start_time'] = time.time()

    bot.send_message(
        chat_id,
        f'❓ <b>{example["question"]} = ?</b>',
        parse_mode='HTML'
    )

    # новый ID вопроса
    user['question_id'] += 1

    current_question_id = user['question_id']

    # запуск таймера
    threading.Thread(
        target=question_timer,
        args=(chat_id, current_question_id),
        daemon=True
    ).start()

# =========================
# ТАЙМЕР ВОПРОСА
# =========================
def question_timer(chat_id, question_id):

    time.sleep(10)

    if chat_id not in users:
        return

    user = users[chat_id]

    # если вопрос всё ещё активен
    if (
        user['active']
        and user['question_id'] == question_id
    ):

        bot.send_message(
            chat_id,
            random.choice(slow_messages)
        )

        # повторяем каждые 10 секунд
        threading.Thread(
            target=question_timer,
            args=(chat_id, question_id),
            daemon=True
        ).start()

# =========================
# ПРОВЕРКА ОТВЕТА
# =========================
@bot.message_handler(func=lambda message: True)
def check_answer(message):

    if message.chat.id not in users:

        bot.send_message(
            message.chat.id,
            '▶️ Нажми /start'
        )

        return

    user = users[message.chat.id]

    if not user['active']:
        return

    example = user['examples'][user['current']]

    try:

        user_answer = float(
            message.text.replace(',', '.')
        )

    except:

        bot.send_message(
            message.chat.id,
            '⚠️ Введи число'
        )

        return

    correct_answer = example['answer']

    # =========================
    # ПРАВИЛЬНЫЙ ОТВЕТ
    # =========================
    if user_answer == correct_answer:

        # считаем время ответа
        response_time = (
            time.time() -
            user['question_start_time']
        )

        user['total_response_time'] += response_time

        user['correct'] += 1

        bot.send_message(
            message.chat.id,
            random.choice(correct_answers)
        )

        # отключаем таймер
        user['question_id'] += 1

        # следующий пример
        user['current'] += 1

        send_question(message.chat.id)

    # =========================
    # НЕПРАВИЛЬНЫЙ ОТВЕТ
    # =========================
    else:

        user['wrong'] += 1

        bot.send_message(
            message.chat.id,
            random.choice(wrong_answers)
        )

# =========================
# ЗАПУСК
# =========================
bot.remove_webhook()

print('BOT STARTED')

bot.polling(none_stop=True)
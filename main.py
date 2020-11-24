from telebot.types import *
from config import *
import telebot, sqlite3, time, threading, datetime
from db_function import *

bot = telebot.TeleBot(token, threaded=True)

back_btn = '⬅️Назад'
main_back_btn = 'Вернуться в основное меню'
mail_but = "Рассылка"
backMail_but = 'Назад ◀️'
preMail_but = 'Предпросмотр 👁'
startMail_but = 'Старт 🏁'
textMail_but = 'Текст 📝'
butMail_but = 'Ссылка-кнопка ⏺'
photoMail_but = 'Фото 📸'


def mail_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[KeyboardButton(name) for name in [textMail_but, photoMail_but]])
    keyboard.add(*[KeyboardButton(name) for name in [butMail_but, preMail_but]])
    keyboard.add(*[KeyboardButton(name) for name in [backMail_but, startMail_but]])
    return keyboard


def admin_keyboard(message=None):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[KeyboardButton(name) for name in [mail_but]])
    keyboard.add(*[KeyboardButton(name) for name in ['Добавить задание']])
    if message:
        bot.clear_step_handler(message)
    return keyboard


def main_keyboard(message=None):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[KeyboardButton(name) for name in ['Активные задания 📗']])
    keyboard.add(*[KeyboardButton(name) for name in ['Баланс 💰']])
    if message:
        bot.clear_step_handler(message)
    return keyboard


def isfloat(x):
    try:
        a = float(x)
    except (TypeError, ValueError):
        return False
    else:
        return True


@bot.message_handler(commands=["admin"], func=lambda m: m.from_user.id in admins)
def admin_command(message: Message):
    bot.send_message(message.chat.id, "Админ меню", reply_markup=admin_keyboard(message))


def mailing(user_ids, lively, banned, deleted, chat_id, mail_text, mail_photo, mail_link, mail_link_text):
    conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
    c = conn.cursor()
    users_block = []
    start_mail_time = time.time()
    c.execute('''SELECT COUNT(*) FROM users''')
    allusers = int(c.fetchone()[0])
    for user_id in user_ids:
        try:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text=mail_link_text, url=mail_link))
            if str(mail_photo) != '0':
                if str(mail_link_text) != '0':
                    bot.send_photo(user_id, caption=mail_text, photo=mail_photo, parse_mode='HTML',
                                   reply_markup=keyboard)
                else:
                    bot.send_photo(user_id, caption=mail_text, parse_mode='HTML', photo=mail_photo)
            else:
                if str(mail_link_text) not in '0':
                    bot.send_message(user_id, text=mail_text, parse_mode='HTML',
                                     reply_markup=keyboard)
                else:
                    bot.send_message(user_id, parse_mode='HTML', text=mail_text)
            lively += 1
        except Exception as e:
            if 'bot was blocked by the user' in str(e):
                users_block.append(user_id)
                banned += 1
                # database is locked
    print(users_block)
    for user_id in users_block:
        c.execute("UPDATE users SET lively = (?) WHERE user_id = (?)", ('block', user_id,))
    admin_text = '*Рассылка окончена! ✅\n\n' \
                 '🙂 Количество живых пользователей:* {0}\n' \
                 '*% от числа всех:* {1}%\n' \
                 '*💩 Количество заблокировавших:* {3}\n' \
                 '*🕓 Время рассылки:* {2}'.format(str(lively), str(round(lively / allusers * 100, 2)),
                                                   str(round(time.time() - start_mail_time, 2)) + ' сек', str(banned))
    bot.send_message(chat_id, admin_text, parse_mode='Markdown', reply_markup=admin_keyboard())
    c.close()
    conn.commit()


def store_task(chat_id, message_id, die_time=0, instruction=0, url=0, price=0, time=0, status=0, counter=0, check=True):
    conn = sqlite3.connect("db/task.db", check_same_thread=False, timeout=10)
    c = conn.cursor()
    if check:
        c.execute(
            "INSERT INTO tasks (user_id, message_id, die_timeTask, instructionTask ,urlTask, priceTask, timeTask) VALUES (?,?,?,?,?,?,?)",
            (chat_id, message_id, die_time, instruction, url, price, time))
    c.close()
    conn.commit()


def send_task_all_users(chat_id):
    conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
    c = conn.cursor()
    users_block = []
    lively, banned = 0, 0
    instruction, url, price, timetask = c.execute(
        "select instructionTask, urlTask, priceTask, timeTask from users where user_id = ?",
        (chat_id,)).fetchone()
    now_time = datetime.datetime.now()
    die_time = now_time + datetime.timedelta(minutes=timetask)
    user_ids = []
    c.execute("""select user_id from users""")
    user_id = c.fetchone()
    while user_id is not None:
        user_ids.append(user_id[0])
        user_id = c.fetchone()
    for user_id in user_ids:
        try:
            keyboard = InlineKeyboardMarkup()

            message = bot.send_message(chat_id, f" 📋 <b>Задание</b>\n\n"
                                                f"📍 <b>Инструкция</b>\n<i>{instruction}</i>\n\n"
                                                f"💵 <b>Цена:</b> {price} рублей\n"
                                                f"⏳ <b>Время:</b> {timetask} минут", parse_mode="HTML",
                                       reply_markup=keyboard, disable_web_page_preview=True)
            if url != 0:
                keyboard.row(InlineKeyboardButton("Выполнить задание", url=url))
            keyboard.row(InlineKeyboardButton("Проверить задание", callback_data=f"checkTask_{message.message_id}"))
            bot.add
            store_task(user_id, message.message_id, die_time, instruction, url, price, timetask)
            lively += 1
        except Exception as e:
            if 'bot was blocked by the user' in str(e):
                users_block.append(user_id)
                banned += 1
    for user_id in users_block:
        c.execute("UPDATE users SET lively = (?) WHERE user_id = (?)", ('block', user_id,))
    admin_text = '*Рассылка задания завершена!* ✅'
    bot.send_message(chat_id, admin_text, parse_mode='Markdown', reply_markup=admin_keyboard())
    c.close()
    conn.commit()


@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    bot.send_message(message.chat.id,
                     "\t\tПривет! Меня зовут <b>Алиса</b>, и я бот, который раздает деньги за выполнение простых заданий в Instagram ⏬"
                     "\n   📌 Подписаться на аккаунт ✏️ \n   📌 Поставить лайк ❤️\n   📌 Подать жалобу 🧨\n\n"
                     "\t<i>За выполнение одного задания я раздаю от 50 до 1000 руб\n"
                     "\tЗадания будут появляться несколько раз в день и будут актуальны <b>СТРОГО ОГРАНИЧЕННОЕ</b> время (10-20 минут), после чего будут удаляться."
                     "Если ты не выполнил задание за это время - деньги ты не получишь. Так что включай уведомления, чтобы не пропустить от меня задание и получить свои деньги.</i>",
                     parse_mode='HTML', disable_web_page_preview=True)


@bot.message_handler(func=lambda m: m.text == mail_but and m.chat.id in admins and m.from_user.id == m.chat.id)
def cheker(message: Message):
    conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)

    def admin_mailing(message: Message):
        chat_id = message.chat.id
        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
        msgtext = message.text
        c = conn.cursor()
        c.execute("""select textMail from users where user_id = %s""" % chat_id)
        textMailUser = str(c.fetchone()[0])
        c.execute("""select photoMail from users where user_id = %s""" % chat_id)
        photoMailUser = str(c.fetchone()[0])
        c.execute("""select butTextMail from users where user_id = %s""" % chat_id)
        butTextMail = str(c.fetchone()[0])
        c.execute("""select butUrlMail from users where user_id = %s""" % chat_id)
        butUrlMail = str(c.fetchone()[0])
        if msgtext == mail_but:
            bot.send_message(chat_id, '*Вы попали в меню рассылки *📢\n\n'
                                      'Для возврата нажмите *{0}*\n\n'
                                      'Для отмены какой-либо операции нажмите /start\n\n'
                                      'Используйте *{1}* для предварительного просмотра рассылки, а *{2}* для начала'
                                      ' рассылки\n\n'
                                      'Текст рассылки поддерживает разметку *HTML*, то есть:\n'
                                      '<b>*Жирный*</b>\n'
                                      '<i>_Курсив_</i>\n'
                                      '<pre>`Моноширный`</pre>\n'
                                      '<a href="ссылка-на-сайт">[Обернуть текст в ссылку](test.ru)</a>'.format(
                backMail_but, preMail_but, startMail_but
            ),
                             parse_mode="markdown", reply_markup=mail_menu())
            bot.register_next_step_handler(message, admin_mailing)

        elif msgtext == backMail_but:
            bot.send_message(chat_id, backMail_but, reply_markup=admin_keyboard(message))
            bot.clear_step_handler(message)

        elif msgtext == preMail_but:
            try:
                if butTextMail == '0' and butUrlMail == '0':
                    if photoMailUser == '0':
                        bot.send_message(chat_id, textMailUser, parse_mode='html', reply_markup=mail_menu())
                    else:
                        bot.send_photo(chat_id, caption=textMailUser, photo=photoMailUser, parse_mode='html',
                                       reply_markup=mail_menu())
                else:
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton(text=butTextMail, url=butUrlMail))
                    if photoMailUser == '0':
                        bot.send_message(chat_id, textMailUser, parse_mode='html',
                                         reply_markup=keyboard)
                    else:
                        bot.send_photo(chat_id, caption=textMailUser, photo=photoMailUser, parse_mode='html',
                                       reply_markup=keyboard)
            except:
                bot.send_message(chat_id, "Упс..проверьте правильность введения данных")
            bot.register_next_step_handler(message, admin_mailing)

        elif msgtext == startMail_but:
            c.execute("""update users set textMail = 0 where user_id = %s""" % chat_id)
            c.execute("""update users set photoMail = 0 where user_id = %s""" % chat_id)
            c.execute("""update users set butTextMail = 0 where user_id = %s""" % chat_id)
            c.execute("""update users set butUrlMail = 0 where user_id = %s""" % chat_id)
            user_ids = []
            c.execute("""select user_id from users""")
            user_id = c.fetchone()
            while user_id is not None:
                user_ids.append(user_id[0])
                user_id = c.fetchone()
            c.close()
            mail_thread = threading.Thread(target=mailing, args=(
                user_ids, 0, 0, 0, chat_id, textMailUser, photoMailUser, butUrlMail, butTextMail))
            mail_thread.start()
            bot.send_message(chat_id, 'Рассылка началась!',
                             reply_markup=admin_keyboard(message))

        elif textMail_but == msgtext:
            def process_textMail(message: Message):
                if message.text:
                    if message.text == "/start":
                        bot.send_message(chat_id, "Действие отменено")
                    else:
                        c = conn.cursor()
                        c.execute("update users set textMail = (?) where user_id = (?)", (message.text,
                                                                                          chat_id))
                        conn.commit()
                        c.close()
                        bot.send_message(chat_id, "Текст успешно установлен")
                    bot.register_next_step_handler(message, admin_mailing)

            bot.send_message(chat_id,
                             'Введите текст рассылки. Допускаются теги HTML. Для отмены ввода нажите /start',
                             reply_markup=mail_menu())
            bot.register_next_step_handler(message, process_textMail)

        elif photoMail_but == msgtext:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(InlineKeyboardButton(text='Добавить фото 📝', callback_data='editPhotoMail'))
            keyboard.row(InlineKeyboardButton(text='Удалить фото ❌', callback_data='deletePhoto'))
            bot.send_message(chat_id, 'Выберите действие ⤵', reply_markup=keyboard)
            bot.register_next_step_handler(message, admin_mailing)

        elif butMail_but == msgtext:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(InlineKeyboardButton(text='Изменить текст кнопки 📝', callback_data='editTextBut'))
            keyboard.row(InlineKeyboardButton(text='Изменить ссылку кнопки 🔗', callback_data='editUrlBut'))
            keyboard.row(InlineKeyboardButton(text='Убрать всё к чертям 🙅‍♂', callback_data='deleteBut'))
            bot.send_message(chat_id, 'Выберите действие ⤵', reply_markup=keyboard)
            bot.register_next_step_handler(message, admin_mailing)

        elif msgtext == "/start":
            bot.clear_step_handler(message)
            start(message)

        else:
            bot.clear_step_handler(message)
            bot.register_next_step_handler(message, admin_mailing)

    user_id = message.chat.id
    c = conn.cursor()
    if c.execute("select * from users where user_id = %s" % user_id).fetchone() is None:
        c.execute("insert into users (user_id, state) values (?, ?)",
                  (user_id, 0))
        conn.commit()
    c.close()
    bot.clear_step_handler(message)
    admin_mailing(message)


@bot.message_handler(
    func=lambda m: m.text in ['Добавить задание'] and m.chat.id in admins and m.from_user.id == m.chat.id)
def update(m):
    if m.text == 'Добавить задание':
        def get_price_task(m):
            if m.content_type == 'text':
                if m.text == '/start':
                    start(m)
                elif m.text == '/admin':
                    admin_command(m)
                elif isfloat(m.text):
                    if float(m.text) > 0:
                        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                        c = conn.cursor()
                        c.execute("update users set priceTask = (?) where user_id = (?)", (m.text,
                                                                                           m.chat.id))
                        instruction, url, price, timetask = c.execute(
                            "select instructionTask, urlTask, priceTask, timeTask from users where user_id = ?",
                            (m.chat.id,)).fetchone()
                        conn.commit()
                        c.close()
                        keyboard = InlineKeyboardMarkup()
                        if url != 0:
                            keyboard.row(InlineKeyboardButton("Выполнить задание", url=url))
                        keyboard.row(InlineKeyboardButton("Проверить задание", callback_data="pass"))
                        try:
                            message = bot.send_message(m.chat.id, f" 📋 <b>Задание</b>\n\n"
                                                                  f"📍 <b>Инструкция</b>\n<i>{instruction}</i>\n\n"
                                                                  f"💵 <b>Цена:</b> {price} рублей\n"
                                                                  f"⏳ <b>Время:</b> {timetask} минут",
                                                       parse_mode="HTML", reply_markup=keyboard,
                                                       disable_web_page_preview=True)
                            keyboard = InlineKeyboardMarkup()
                            keyboard.row(InlineKeyboardButton("Публикация",
                                                              callback_data=f"publicationTask_{message.message_id}"))
                            keyboard.row(
                                InlineKeyboardButton("Удалить", callback_data=f"removeTask_{message.message_id}"))
                            bot.send_message(m.chat.id, "Выберите действие ⬇️", reply_markup=keyboard)

                        except:
                            bot.send_message(m.chat.id, "🚫 Проверьте правильность ввода данных и начните заново")
                    else:
                        bot.send_message(m.chat.id, "Спробуйте еще раз:")
                        bot.register_next_step_handler(message=m, callback=get_price_task)
                else:
                    bot.send_message(m.chat.id, "Спробуйте еще раз:")
                    bot.register_next_step_handler(message=m, callback=get_price_task)

            else:
                bot.send_message(m.chat.id, "Спробуйте еще раз:")
                bot.register_next_step_handler(message=m, callback=get_price_task)

        def get_time_task(m):
            if m.content_type == 'text':
                if m.text == '/start':
                    start(m)
                elif m.text == '/admin':
                    admin_command(m)
                elif m.text.isdigit():
                    if int(m.text) > 0:
                        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                        c = conn.cursor()
                        c.execute("update users set timeTask = (?) where user_id = (?)", (m.text,
                                                                                          m.chat.id))
                        conn.commit()
                        c.close()
                        bot.send_message(m.chat.id, '💲 Введите цену за задание в рублях:')
                        bot.register_next_step_handler(message=m, callback=get_price_task)
                    else:
                        bot.send_message(m.chat.id, "Спробуйте еще раз:")
                        bot.register_next_step_handler(message=m, callback=get_time_task)
                else:
                    bot.send_message(m.chat.id, "Спробуйте еще раз:")
                    bot.register_next_step_handler(message=m, callback=get_time_task)

            else:
                bot.send_message(m.chat.id, "Спробуйте еще раз:")
                bot.register_next_step_handler(message=m, callback=get_time_task)

        def get_url_task(m):
            if m.content_type == 'text':
                if m.text == '/start':
                    start(m)
                elif m.text == '/admin':
                    admin_command(m)
                else:
                    conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                    c = conn.cursor()
                    if m.text != "/next":
                        c.execute("update users set urlTask = (?) where user_id = (?)", (m.text,
                                                                                         m.chat.id))
                    else:
                        c.execute("update users set urlTask = (?) where user_id = (?)", (0,
                                                                                         m.chat.id))
                    conn.commit()
                    c.close()
                    bot.send_message(m.chat.id, '⏱ Введите время выполнения задания в минутах:')
                    bot.register_next_step_handler(message=m, callback=get_time_task)
            else:
                bot.send_message(m.chat.id, "Спробуйте еще раз:")
                bot.register_next_step_handler(message=m, callback=get_url_task)

        def get_instruction_task(m):
            if m.content_type == 'text':
                if m.text == '/start':
                    start(m)
                elif m.text == '/admin':
                    admin_command(m)
                else:
                    conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                    c = conn.cursor()
                    c.execute("update users set instructionTask = (?) where user_id = (?)", (m.text,
                                                                                             m.chat.id))
                    conn.commit()
                    c.close()
                    bot.send_message(m.chat.id,
                                     '⏹ Введите ссылку для кнопки: \n\nНажмите /next если хотите пропустить:')
                    bot.register_next_step_handler(message=m, callback=get_url_task)

            else:
                bot.send_message(m.chat.id, "Спробуйте еще раз:")
                bot.register_next_step_handler(message=m, callback=get_instruction_task)

        bot.send_message(m.chat.id, "✒️ Введите инструкцию для задания:")
        bot.clear_step_handler(m)
        bot.register_next_step_handler(message=m, callback=get_instruction_task)


@bot.callback_query_handler(func=lambda c: c.data)
def callback(callback_query: telebot.types.CallbackQuery):
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    if 'editTextBut' in callback_query.data:
        bot.clear_step_handler(callback_query.message)

        def process_editTextBut(message: Message):
            if message.text:
                conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                c = conn.cursor()
                # c.execute("""update users set state = 0 where user_id = %s""" % (chat_id))
                c.execute("update users set butTextMail = (?) where user_id = (?)", (message.text,
                                                                                     chat_id))
                conn.commit()
                c.close()
                bot.send_message(chat_id, 'Текст кнопки обновлен! ✅', reply_markup=mail_menu())

        bot.send_message(chat_id, "Введите текст для кнопки")
        bot.register_next_step_handler(callback_query.message, process_editTextBut)

    elif 'editUrlBut' in callback_query.data:
        def process_editUrlBut(message: Message):
            if message.text:
                conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                c = conn.cursor()
                c.execute("update users set butUrlMail = (?) where user_id = (?)", (message.text,
                                                                                    chat_id))
                conn.commit()
                c.close()
                bot.send_message(chat_id, 'Ссылка кнопки обновлена! ✅', reply_markup=mail_menu())
                cheker(message)

        bot.clear_step_handler(callback_query.message)
        bot.send_message(chat_id, 'Введите ссылку 📝', reply_markup=mail_menu())
        bot.register_next_step_handler(callback_query.message, process_editUrlBut)

    elif 'deleteBut' in callback_query.data:
        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
        c = conn.cursor()
        c.execute("""update users set butUrlMail = 0 where user_id = (?)""", (chat_id,))
        c.execute("""update users set butTextMail = 0 where user_id = (?)""", (chat_id,))
        conn.commit()
        c.close()
        bot.send_message(chat_id, 'Удалено! 🗑', reply_markup=mail_menu())
        cheker(callback_query.message)

    elif 'editPhotoMail' in callback_query.data:
        def wait_photo(message: Message):
            if message.content_type == 'photo':
                conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
                c = conn.cursor()
                msgphoto = message.json['photo'][0]['file_id']
                c.execute("""update users set photoMail = (?) where user_id = (?)""", (msgphoto, chat_id,))
                bot.send_message(chat_id, 'Фото прикреплено! ✅', reply_markup=mail_menu())
                conn.commit()
                c.close()
                bot.register_next_step_handler(message, cheker)
            else:
                bot.send_message(chat_id, "Упс...", reply_markup=mail_menu())
                bot.register_next_step_handler(message, cheker)

        bot.clear_step_handler(callback_query.message)
        bot.send_message(chat_id, 'Отправьте фотографию', reply_markup=mail_menu())
        bot.register_next_step_handler(callback_query.message, wait_photo)

    elif 'deletePhoto' in callback_query.data:
        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
        c = conn.cursor()
        c.execute("""update users set photoMail = 0 where user_id = (?)""", (chat_id,))
        conn.commit()
        c.close()
        bot.send_message(chat_id, 'Фото удалено! ✅', reply_markup=mail_menu())
        cheker(callback_query.message)
    elif 'removeTask' in callback_query.data:
        id_message = int(str(callback_query.data).split("_")[1])

        conn = sqlite3.connect("db/user.db", check_same_thread=False, timeout=10)
        c = conn.cursor()
        c.execute("update users set instructionTask = (?) where user_id = (?)", (0,
                                                                                 callback_query.message.chat.id))
        c.execute("update users set urlTask = (?) where user_id = (?)", (0,
                                                                         callback_query.message.chat.id))
        c.execute("update users set priceTask = (?) where user_id = (?)", (0,
                                                                           callback_query.message.chat.id))
        c.execute("update users set timeTask = (?) where user_id = (?)", (0,
                                                                          callback_query.message.chat.id))
        conn.commit()
        c.close()
        bot.delete_message(callback_query.from_user.id, message_id=id_message)
        bot.edit_message_text("Удалено...", callback_query.from_user.id, callback_query.message.message_id)
    elif 'publicationTask' in callback_query.data:
        chat_id = callback_query.message.chat.id
        id_message = int(str(callback_query.data).split("_")[1])
        task_thread = threading.Thread(target=send_task_all_users, args=(chat_id,))
        task_thread.start()
        bot.delete_message(chat_id, message_id=id_message)
        bot.edit_message_text("Рассылка задания началась! Дождитесь окончания процесса.", callback_query.from_user.id,
                              callback_query.message.message_id)
    elif 'checkTask' in callback_query.data:
        message_id = int(str(callback_query.data).split("_")[1])
        chat_id = callback_query.from_user.id
        conn = sqlite3.connect("db/task.db", check_same_thread=False, timeout=10)
        c = conn.cursor()
        count = int(c.execute("SELECT counter FROM tasks WHERE user_id = ? and message_id = ?",
                              (chat_id, message_id)).fetchone()[0])
        if count == 0:
            bot.answer_callback_query(callback_query.id, "Cначала выполните задание")
        else:
            pass


if __name__ == '__main__':
    bot.polling(none_stop=True)
    """
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            pass
            print(e)
    """

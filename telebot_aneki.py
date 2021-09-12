import telebot
from telebot import types
import pymysql.cursors
import random
import re
import cryptography

# открываем файл с токеном на чтение и считываем токен
reader = open('token.txt', 'r')
TOKEN = reader.read()

# это не понадобится, здесь подключение к моей БД
def set_connection():
    connection = pymysql.connect(
    host='localhost',
    user='anekiuser',
    password='password',
    database='testbase',
    cursorclass=pymysql.cursors.DictCursor)
    return connection

cat_list = []

# это тоже не понадобится
con = set_connection()
with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM aneki")
        rows = cur.fetchall()
        for row in rows:
            if (cat_list.count(row['category']) == 0):
                cat_list.append(row['category'])

cat_list_index = 0

# инициализация объекта бота по считанному из файла токену
bot = telebot.TeleBot(TOKEN)


# обработчик события: если боту придет команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # создаем клавиатуру, make_actions_keyboard - моя функция, возвращает объект клавы
    # и находится ниже
    keyboard = make_actions_keyboard()
    # вызывается метод объекта бота с параметрами id чата, текстом сообщения и конфигом клавиатуры ответа
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

# обработчик события: если пришло любое сообщение
@bot.message_handler(func=lambda message: True)
def echo_all(message):
        if ( (message.text).lower() == 'анекдот' or (message.text).lower() == 'случайный анекдот' ):
            get_random_anek(message)
        if ( (message.text).lower() == 'привет' ):
            # отправляет стикер с этим страшным, но уникальным кодом
            bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAICuGAFbIN6JoyAB3kuJua4qsxHnsA_AAKBAAM0hYUM0PCQYxMGHxYeBA")
        if ( (message.text).lower() == 'категории' ):
            get_categories(message)

# обработчик события нажатия на кнопку в inline-клавиатуре:
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global cat_list_index
    # если была нажата кнопка, передающая значение 'next'
    if call.data == 'next':
        # удаление сообщения
        bot.delete_message(call.message.chat.id, call.message.message_id)
        cat_list_index += 5
        # создание клавиатуры
        keyboard = make_categories_keyboard(cat_list_index)
        # отправка сообщения
        bot.send_message(call.message.chat.id,'Категории:', reply_markup=keyboard)
    # дальше аналогично
    elif call.data =='prev':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        cat_list_index -= 5
        keyboard = make_categories_keyboard(cat_list_index)
        bot.send_message(call.message.chat.id,'Категории:', reply_markup=keyboard)
    elif call.data == '1':
        set_rating(1, call)
    elif call.data == '2':
        set_rating(2, call)
    elif call.data == '3':
        set_rating(3, call)
    elif call.data == '4':
        set_rating(4, call)
    elif call.data == '5':
        set_rating(5, call)
    elif call.data == 'report_format':
        report_format(call)
    elif call.data == 'report_anek':
        report_anek(call)
    else:
        get_category_anek(call)


# это не нужно
def set_rating(rating, call):
        con = set_connection()
        with con:
            cur = con.cursor()
            current_id = take_id_from_anek(call.message.text)
            print("Новая оценка анекдота с id = ", current_id)
            sql_str = "SELECT * FROM aneki where id=%s"
            cur.execute(sql_str, current_id)
            row = cur.fetchone()
            sum_rating = row['sum']
            people = row['people']
            previous_rate = "Были сумма оценок: " + str(sum_rating) + " кол-во оценивших: " + str(people)
            sum_rating += rating
            people += 1
            vals = (sum_rating, people, current_id)
            sql_str = "UPDATE aneki SET sum=%s, people=%s WHERE id=%s"
            cur.execute(sql_str, vals)
            now_rate = "Стали сумма оценок: " + str(sum_rating) + " кол-во оценивших: " + str(people) + " средняя: " + str(sum_rating/people)
            print(previous_rate)
            print(now_rate)
            con.commit()
            cur.close()
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id-1)
        except:
            pass
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
        bot.send_message(call.message.chat.id, "Спасибо за оценку!")


# это тоже не нужно
def take_id_from_anek(text):
        current_id = re.findall('№\d+', text)[0]
        current_id = current_id.replace('№', '')
        return current_id

# здесь есть нужное в конце, но оно такое же, как и раньше
def get_random_anek(message):
    con = set_connection()
    with con:
        cur = con.cursor()
        number = random.randint(1, 130263)
        cur.execute("SELECT * FROM aneki WHERE id=%s", number)
        row = cur.fetchone()
        con.commit()
        cur.close()
        string = "Анекдот №" + str(row['id']) + "\n\n" + row['anek']
    print("Вызван случайный анекдот, категория: " + row['category'] + " с id = " + str(row['id']))
    keyboard = make_rating_and_feedback_keyboard()
    bot.send_message(message.chat.id, "Оцените анекдот:", reply_markup=None)
    bot.send_message(message.chat.id, string, reply_markup=keyboard)


# здесь есть нужное
def get_category_anek(call):
    for cat in cat_list:
        if (call.data.lower() == cat.lower()):
            cat_name = cat
            break
    con = set_connection()
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM aneki WHERE category=%s", cat_name)
        rows = cur.fetchall()
        number = random.randint((rows[0])['id'], (rows[len(rows)-1])['id'])
        cur.execute("SELECT * FROM aneki WHERE id=%s", number)
        row = cur.fetchone()
        cur.execute("UPDATE aneki SET views=%s", row['views']+1)
        cur.close()
        string = "Анекдот №" + str(row['id']) + "\n\n" + row['anek']
    print("Вызван анекдот по категории: " + call.data + " с id = " + str(row['id']))
    # редактирование сообщения, по ключевым параметрам все понятно, думаю
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Оцените анекдот: ", reply_markup=None)
    keyboard = make_rating_and_feedback_keyboard()
    bot.send_message(call.message.chat.id, string, reply_markup=keyboard)

# здесь уже все было
def get_categories(message):
    global cat_list_index
    cat_list_index = 0
    keyboard = make_categories_keyboard(cat_list_index)
    bot.send_message(message.chat.id,'Категории:', reply_markup=None)
    bot.delete_message(message.chat.id, message.message_id+1)
    bot.send_message(message.chat.id,'Категории:', reply_markup=keyboard)

# функция создания клавиатуры категорий
def make_categories_keyboard(index):
    # эта клавиатура будет inline, а не reply
    # то есть будет располагаться непосредственно в чате
    keyboard = types.InlineKeyboardMarkup()
    k = 0
    # здесь перерисовывается клава в зависимости от просматриваемой зоны листа
    # обрати внимание на параметр callback_data, он был выше в обработчике коллбэка
    while index < len(cat_list):
        if (k >= 5):
            buttonNext = types.InlineKeyboardButton(text=">", callback_data='next')
            buttonPrev = types.InlineKeyboardButton(text="<", callback_data='prev')
            keyboard.add(buttonPrev, buttonNext)
            break
        else:
            button=types.InlineKeyboardButton(text=cat_list[index],callback_data=cat_list[index])
            keyboard.add(button)
        k += 1
        index += 1
    global cat_list_index
    if (index >= len(cat_list)-1):
        cat_list_index = -5
        button = types.InlineKeyboardButton(text=">", callback_data='next')
        keyboard.add(button)
    return keyboard

# функция создания клавиатуры действий
def make_actions_keyboard():
    # эта клавиатура будет reply
    # то есть будет располагаться на месте твоей обычной клавы
    # но вместо букв там будут создаваемые нами кнопки
    keyboard = types.ReplyKeyboardMarkup(True)
    itembtnRandomAnek = types.KeyboardButton('Случайный анекдот')
    itembtnCategories = types.KeyboardButton('Категории')
    keyboard.row(itembtnRandomAnek, itembtnCategories)
    return keyboard

# функция создания клавиатуры оценки и репортов
# тут аналогичная inline клавиатура
def make_rating_and_feedback_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='1', callback_data='1')
    button2 = types.InlineKeyboardButton(text='2', callback_data='2')
    button3 = types.InlineKeyboardButton(text='3', callback_data='3')
    button4 = types.InlineKeyboardButton(text='4', callback_data='4')
    button5 = types.InlineKeyboardButton(text='5', callback_data='5')
    keyboard.row(button1, button2, button3, button4, button5)
    buttonReportFormat = types.InlineKeyboardButton(text='Кривой формат', callback_data='report_format')
    buttonReportAnek = types.InlineKeyboardButton(text="Not funny, didn't laugh", callback_data='report_anek')
    keyboard.row(buttonReportFormat, buttonReportAnek)
    return keyboard

# функция создания клавиатуры только оценки для замещения клавы с репортами
# мне было лень искать как удалять кнопки отдельно
def make_rating_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='1', callback_data='1')
    button2 = types.InlineKeyboardButton(text='2', callback_data='2')
    button3 = types.InlineKeyboardButton(text='3', callback_data='3')
    button4 = types.InlineKeyboardButton(text='4', callback_data='4')
    button5 = types.InlineKeyboardButton(text='5', callback_data='5')
    keyboard.row(button1, button2, button3, button4, button5)
    return keyboard


# это не нужно
def report_format(call):
    con = set_connection()
    with con:
        current_id = take_id_from_anek(call.message.text)
        cur = con.cursor()
        cur.execute("SELECT * FROM aneki WHERE id=%s", current_id)
        row = cur.fetchone()
        anek_str = row['anek']
        cur.execute("select count(*) FROM reportedaneki WHERE id = %s", current_id)
        row = cur.fetchone()
        if (row['count(*)'] == 0):
            vals = (current_id, 'format', anek_str)
            cur.execute("INSERT INTO reportedaneki (id, reporttype, anek) VALUES (%s, %s, %s)", vals)
            print("ЗАРЕПОРЧЕННЫЙ ПО ФОРМАТУ АНЕКДОТ С ID = " + str(current_id))
        con.commit()
        cur.close()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=make_rating_keyboard())
    bot.send_message(chat_id=call.message.chat.id, text='Спасибо за обратную связь!', reply_markup=None)

# это не нужно
def report_anek(call):
    con = set_connection()
    with con:
        current_id = take_id_from_anek(call.message.text)
        cur = con.cursor()
        cur.execute("SELECT * FROM aneki WHERE id=%s", int(current_id))
        row = cur.fetchone()
        anek_str = row['anek']
        cur.execute("select count(*) FROM reportedaneki WHERE id = %s", int(current_id))
        row = cur.fetchone()
        if (row['count(*)'] == 0):
            vals = (current_id, 'notfunny', anek_str)
            cur.execute("INSERT INTO reportedaneki (id, reporttype, anek) VALUES (%s, %s, %s)", vals)
            print("ЗАРЕПОРЧЕННЫЙ ПО КАЧЕСТВУ АНЕКДОТ С ID = " + str(current_id))
        con.commit()
        cur.close()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
    bot.send_message(chat_id=call.message.chat.id, text='Спасибо за обратную связь!', reply_markup=None)

# здесь bot.polling означает, что бот начинает свою работу
# поллинг это когда бот регулярно посылает запросы на сервер
# чтобы проверить обновления инфы
# в качестве большого релиза так делать нехорошо
# потому что идет нагрузка на сервы тг, неприлично
# подходит только для домашнего дебага
bot.polling(none_stop=True)
# сразу забиваем клавиатуру действий
keyboard = types.ReplyKeyboardMarkup(True)
itembtnRandomAnek = types.KeyboardButton('Случайный анекдот')
itembtnCategories = types.KeyboardButton('Категории')
keyboard.row(itembtnRandomAnek, itembtnCategories)
# это нужно, чтобы у нас не прекращалось все действо
while True:
    pass

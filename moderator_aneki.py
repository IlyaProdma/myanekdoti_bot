import telebot
from telebot import types
import pymysql.cursors
import re
import cryptography

reader = open('modertoken.txt', 'r')
TOKEN = reader.read()

def set_connection():
    connection = pymysql.connect(
    host='localhost',
    user='moderator',
    password='moderpassword',
    database='testbase',
    cursorclass=pymysql.cursors.DictCursor)
    return connection

moder_id_list = [219543985, 376854165, 693270678, 261718160]
#moder_id_list = [376854165]

bot = telebot.TeleBot(TOKEN)

isredacting = False

def take_id_from_anek(text):
        current_id = re.findall('№\d+', text)[0]
        current_id = current_id.replace('№', '')
        return current_id

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = make_actions_keyboard()
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.chat.id in moder_id_list)
def echo_all(message):
    global isredacting
    if (isredacting == True):
        redact_anek(message)
    else:
        if (message.text.lower() == 'показать хреновый анекдот'):
            show_not_funny(message)
        if (message.text.lower() == 'показать кривой анекдот'):
            show_wrong_format(message)

@bot.message_handler(func=lambda message: message.chat.id not in moder_id_list)
def echo_all(message):
    print(message.chat.id)
    bot.send_message(chat_id=message.chat.id, text="Извините, у Вас нет доступа к модерированию. Возможно вы искали бота с анекдотами: @myanekdoti_bot")
        

@bot.callback_query_handler(func=lambda call: call.message.chat.id in moder_id_list)
def callback_worker(call):
    if (call.data == 'redact_anek'):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
        bot.send_message(call.message.chat.id, "Введите вашу версию анекдота. ПОЖАЛУЙСТА, ИЗМЕНЯЙТЕ ТОЛЬКО ТЕКСТ АНЕКДОТА, НЕ МЕНЯЙТЕ СТРОКУ С ID: ", reply_markup=None)
        global isredacting
        isredacting = True
    if (call.data == 'leave_anek'):
        leave_anek(call)
    if (call.data == 'delete_anek'):
        delete_anek(call)


def show_not_funny(message):
    con = set_connection()
    with con:
        cur = con.cursor()
        cur.execute("select * FROM reportedaneki WHERE reporttype='notfunny'")
        row = cur.fetchone()
        con.commit()
        cur.close()
    if (row == None):
        bot.send_message(chat_id=message.chat.id, text='Нет хреновых анеков)', reply_markup = None)
    else:
        string = "Анекдот №" + str(row['id']) + "\n\n" + row['anek']
        keyboard = not_funny_keyboard()
        bot.send_message(chat_id=message.chat.id, text=string, reply_markup=keyboard)

def show_wrong_format(message):
    con = set_connection()
    with con:
        cur = con.cursor()
        cur.execute("select * FROM reportedaneki WHERE reporttype='format'")
        row = cur.fetchone()
        con.commit()
        cur.close()
    if (row == None):
        bot.send_message(chat_id=message.chat.id, text='Нет кривых анеков)', reply_markup = None)
    else:
        string = "Анекдот №" + str(row['id']) + "\n\n" + row['anek']
        keyboard = wrong_format_keyboard()
        bot.send_message(chat_id=message.chat.id, text=string, reply_markup=keyboard)

def leave_anek(call):
    con = set_connection()
    with con:
        cur = con.cursor()
        current_id = take_id_from_anek(call.message.text)
        cur.execute("delete from reportedaneki where id=%s", current_id)
        con.commit()
        cur.close()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
    keyboard = make_actions_keyboard()
    bot.send_message(chat_id=call.message.chat.id, text="Анекдот был оставлен", reply_markup=keyboard)

def delete_anek(call):
    con = set_connection()
    with con:
        cur = con.cursor()
        current_id = take_id_from_anek(call.message.text)
        cur.execute("select * from reportedaneki where id=%s", current_id)
        row = cur.fetchone()
        cur.execute("delete from reportedaneki where id=%s", current_id)
        cur.execute("select * from blacklist where id=%s", current_id)
        temprow = cur.fetchone()
        keyboard = make_actions_keyboard()
        if (temprow == None):
            vals = (row['id'], row['anek'])
            cur.execute("insert into blacklist (id, anek) VALUES (%s, %s)", vals)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
            bot.send_message(chat_id=call.message.chat.id, text="Хреновый анекдот был добавлен в блэклист", reply_markup=keyboard)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup=None)
            bot.send_message(chat_id=call.message.chat.id, text="Этот анекдот уже был в блэклисте", reply_markup=keyboard)
        con.commit()
        cur.close()

def redact_anek(message):
    con = set_connection()
    with con:
        cur = con.cursor()
        current_id = take_id_from_anek(message.text)
        string = re.sub("Анекдот №\d+\n\n", '', message.text)
        print(string)
        vals = (string, current_id)
        cur.execute("update aneki set anek=%s where id=%s", vals)
        cur.execute("delete from reportedaneki where id=%s", current_id)
        con.commit()
        cur.close()
    keyboard = make_actions_keyboard()
    bot.send_message(chat_id=message.chat.id, text="Анекдот был изменен.", reply_markup=keyboard)
    global isredacting
    isredacting = False
        


def make_actions_keyboard():
    keyboard = types.ReplyKeyboardMarkup(True)
    itembtnFormatAnek = types.KeyboardButton('Показать кривой анекдот')
    itembtnBadAnek = types.KeyboardButton('Показать хреновый анекдот')
    keyboard.row(itembtnFormatAnek, itembtnBadAnek)
    return keyboard

def wrong_format_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    buttonRedact = types.InlineKeyboardButton(text='Редактировать', callback_data='redact_anek')
    buttonDelete = types.InlineKeyboardButton(text='Оставить', callback_data='leave_anek')
    keyboard.row(buttonRedact)
    keyboard.row(buttonDelete)
    return keyboard

def not_funny_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    buttonLeave = types.InlineKeyboardButton(text='Оставить', callback_data='leave_anek')
    buttonDelete = types.InlineKeyboardButton(text='В чс', callback_data='delete_anek')
    keyboard.row(buttonLeave)
    keyboard.row(buttonDelete)
    return keyboard


bot.polling(none_stop=True)
keyboard = types.ReplyKeyboardMarkup(True)
itembtnFormatAnek = types.KeyboardButton('Показать кривой анекдот')
itembtnBadAnek = types.KeyboardButton('Показать хреновый анекдот')
keyboard.row(itembtnFormatAnek, itembtnBadAnek)
while True:
    pass

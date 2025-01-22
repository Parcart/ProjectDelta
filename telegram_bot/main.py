import math
import os
import re
import subprocess
from datetime import datetime

import telebot
from dotenv import load_dotenv
from pydantic import EmailStr
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from telegram_bot.Middleware import Middleware
from telegram_bot.Text import text
from telegram_bot.User import User
from email_validator import validate_email, EmailNotValidError

load_dotenv()
print("START")


class ExHandler(telebot.ExceptionHandler):
    def handle(self, exception: Exception):
        print(exception)


def generate_main_menu():
    markup_main = ReplyKeyboardMarkup(resize_keyboard=True)
    markup_main.add(text["button_profile"])
    markup_main.add(text["button_info"])
    return markup_main


if os.environ.get('TG_TOKEN') is None:
    print("TG_TOKEN not set")
    exit(1)

if os.environ.get('REST') is None:
    os.environ['REST'] = 'http://localhost:8080'
print(os.environ['REST'])

bot = telebot.TeleBot(os.environ['TG_TOKEN'], use_class_middlewares=True)
bot.setup_middleware(Middleware())
User._bot = bot


# bot.exception_handler = ExHandler()


@bot.message_handler(commands=['start'])
def start(message, data):
    user = data["user"]
    user.send(text["welcome_back"], generate_main_menu())


@bot.callback_query_handler(func=lambda call: call.data == 'registration')
def start_registration(call, data):
    user: User = data["user"]
    bot.edit_message_text(call.message.text, chat_id=call.message.chat.id, message_id=call.message.id,
                          reply_markup=InlineKeyboardMarkup())
    if user.auth is not None:
        user.send(text["welcome_back"], generate_main_menu())
        return
    msg = bot.send_message(user.id, text["start_registration"],
                           reply_markup=ReplyKeyboardRemove())
    check_registration_fields(msg, user, User.UserRegistrationFrom())


def check_registration_fields(message, user: User, user_form: User.UserRegistrationFrom):
    if user_form.username is None:
        msg = bot.send_message(user.id, text["get_name"])
        bot.register_next_step_handler(msg, set_username, user, user_form)
        return
    if user_form.email is None:
        msg = bot.send_message(user.id, text["get_email"])
        bot.register_next_step_handler(msg, set_email, user, user_form)
        return

    code = user.registration(user_form)
    if code == 200:
        inline_markup = InlineKeyboardMarkup()
        inline_markup.add(InlineKeyboardButton(text["button_confirm"], callback_data="verification_code"))
        msg = user.send(text["confirm_email"], inline_markup)
        bot.register_next_step_handler(msg, confirm_verification_email_code, user)
        return
    if code == 400:
        msg = user.send(
            text['find_ac'])
        bot.register_next_step_handler(msg, link_telegram, user, user_form)
    elif code == 422:
        user.service_unavailable()
    else:
        user.service_unavailable()


def link_telegram(message, user: User, user_form: User.UserRegistrationFrom):
    code = message.text
    result = user.link_telegram(user_form.email, code)
    if result == 200:
        user.send(text["finish_link"], generate_main_menu())
    elif result == 400:
        inline_markup = InlineKeyboardMarkup()
        inline_markup.add(InlineKeyboardButton(text['retry_send_code'], callback_data="send_link_code"))
        user.send(text['bad_code'], keyboard=inline_markup)
    elif result == 409:
        user.send(text['already_link'])
    else:
        user.send(text['service_unavailable'])


@bot.callback_query_handler(func=lambda call: call.data == 'send_link_code')
def send_link_code(call, data):
    user: User = data["user"]
    bot.edit_message_text(call.message.text, chat_id=call.message.chat.id, message_id=call.message.id,
                          reply_markup=InlineKeyboardMarkup())
    if user.send_link_telegram_code():
        inline_markup = InlineKeyboardMarkup()
        inline_markup.add(InlineKeyboardButton(text['retry_send_code'], callback_data="send_link_code"))
        msg = user.send(text['confirm_code'], keyboard=inline_markup)
        bot.register_next_step_handler(msg, link_telegram, user)
    else:
        user.send(text['service_unavailable'])


def set_username(message, user: User, user_form: User.UserRegistrationFrom):
    def is_valid_utf8_string(s):
        if 2 <= len(s) <= 16 and re.fullmatch(r'[^\s]+', s):
            try:
                return True
            except UnicodeEncodeError:
                return False
        return False

    username = message.text

    if not is_valid_utf8_string(username):
        msg = bot.send_message(user.id,
                               text['bad_name'])
        bot.register_next_step_handler(msg, set_username, user, user_form)
        return

    user_form.username = username
    check_registration_fields(message, user, user_form)


def set_email(message, user: User, user_form: User.UserRegistrationFrom):
    email = message.text
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        msg = bot.send_message(user.id, text['bad_email'])
        bot.register_next_step_handler(msg, set_email, user, user_form)
        return

    user_form.email = email
    check_registration_fields(message, user, user_form)


@bot.callback_query_handler(func=lambda call: call.data == 'verification_code')
def start_verification_email(call, data):
    user: User = data["user"]
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    bot.edit_message_text(call.message.text, chat_id=call.message.chat.id, message_id=call.message.id,
                          reply_markup=InlineKeyboardMarkup())

    user.send_verification_email_code()

    inline_markup = InlineKeyboardMarkup()
    inline_markup.add(InlineKeyboardButton(text['button_retry_send_code'], callback_data="verification_code"))
    msg = user.send(text['send_code'], keyboard=inline_markup)
    bot.register_next_step_handler(msg, confirm_verification_email_code, user)


def confirm_verification_email_code(message, user: User):
    code = message.text
    result = user.confirm_verification_code(code)
    if result == 200:
        user.send("Добро пожаловать :)", generate_main_menu())
    elif result == "EmailAlreadyVerified":
        user.send(text['already_email'])
    elif result == "Wrong code":
        msg = user.send(text['bad_code'])
        bot.register_next_step_handler(msg, confirm_verification_email_code, user)
    else:
        inline_markup = InlineKeyboardMarkup()
        inline_markup.add(InlineKeyboardButton(text['button_retry_send_code'], callback_data="verification_code"))
        user.send(text['bad_code'], keyboard=inline_markup)
        bot.register_next_step_handler(message, confirm_verification_email_code, user)


@bot.message_handler(content_types=["text"], func=lambda message: message.text == text['button_profile'])
def open_profile(message, data):
    user: User = data["user"]
    profile = user.profile()
    profile_text = text['text_profile'].format(
        name=profile.name,
        balance=profile.balance
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text['button_add_balance'], callback_data="add_balance"))
    markup.add(InlineKeyboardButton(text['button_transactions'], callback_data="transactions"))
    user.send(profile_text, markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_balance')
def much_add_balance(call, data):
    user: User = data["user"]
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(text['button_back'])
    msg = user.send(text['add_balance'], markup)
    bot.register_next_step_handler(msg, add_balance, user)
    bot.answer_callback_query(call.id)


def add_balance(message, user: User):
    if message.text == text['button_back']:
        profile = user.profile()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['button_add_balance'], callback_data="add_balance"))
        markup.add(InlineKeyboardButton(text['button_transactions'], callback_data="transactions"))
        user.send(text['text_profile'].format(
            name=profile.name,
            balance=profile.balance
        ), markup)
        return
    try:
        balance = int(message.text)
        user.add_balance(balance)
        user.send(text['balance_added'].format(balance=balance), generate_main_menu())
    except ValueError:
        msg = user.send(text['bad_balance'])
        bot.register_next_step_handler(msg, add_balance, user)
        return


@bot.callback_query_handler(func=lambda call: call.data == 'transactions')
def get_transactions(call, data):
    user: User = data["user"]
    transactions = user.read_transactions()
    send_text = text['text_transactions']
    if len(transactions) == 0:
        send_text += "\n\nНет операций"
    else:
        for transaction in transactions:
            send_text += f"\n\n{transaction.created_at} №{transaction.id} {transaction.transaction_type.value} {transaction.description}: {transaction.amount}"

    user.send(send_text)
    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['document', 'audio', 'video', 'voice'])
def processing_audio(message, data):
    user: User = data["user"]
    if message.content_type == 'voice':
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    elif message.content_type == 'audio':
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    elif message.content_type == 'video':
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    elif message.content_type == 'document':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    else:
        return

    try:
        process = subprocess.Popen(
            ['ffmpeg',
             '-i', 'pipe:0',
             '-acodec', 'pcm_s16le',
             '-ar', '16000',
             '-ac', '1',
             '-vn',
             '-y',
             '-f', 's16le',
             '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(input=downloaded_file)
        output = stderr.decode('utf-8')
        output = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', output).group(1)
        time_obj = datetime.strptime(output, '%H:%M:%S.%f')
        total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000
        duration = int(math.floor(total_seconds))
    except Exception as e:
        print(f"Произошла ошибка при обработке аудио: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке файла")
        raise e

    if user.profile().balance < duration:
        user.send("Недостаточно средств")
        return

    result = user.transcribe(stdout)

    if result.get("result"):
        bot.reply_to(message, "Текст: " + result.get("result"))
    else:
        print(f"Произошла ошибка при обработке аудио: {result.get('error')}")
        bot.reply_to(message, "При транскрипции произошла ошибка")



@bot.message_handler(func=lambda message: True)
def message_handler(message, data):
    user: User = data["user"]
    user.send("ЫЫЫЫ", generate_main_menu())


if __name__ == '__main__':
    bot.infinity_polling()

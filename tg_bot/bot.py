import telebot
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, 'Привет! Я твой бот по поиску ссылок на скачивание музыки!\nЧтобы скачать песню, введи /search\nЧтобы узнать, что умеет бот, введи /help или /about')
    
@bot.message_handler(commands=['help', 'about'])
def help_command(message):
    bot.reply_to(message, 'Раздел помощи. Информация о боте')

@bot.message_handler(commands=['search'])
def search_command(message):
    bot.reply_to(message, 'Какую песню хочешь скачать?')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    response = f"Ищем песню {message.text}"
    bot.send_message(message.chat.id, response)

bot.polling()
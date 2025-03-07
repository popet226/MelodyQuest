from dotenv import load_dotenv
import django
import os
import telebot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_searcher.settings')
django.setup()

from searcher.views import search_song

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Флаг для отслеживания состояния работы бота
is_bot_active = False


@bot.message_handler(commands=['start'])
def start_command(message):
    global is_bot_active
    if not is_bot_active:
        bot.reply_to(message, 'Привет! Я твой бот по поиску музыки. Чтобы начать поиск, введи /search.\n Чтобы узнать, что умеет бот, введи /help или /about')
        is_bot_active = True
    else:
        bot.reply_to(message, 'Бот уже активен. Чтобы остановить, введи /stop.')

@bot.message_handler(commands=['stop'])
def stop_command(message):
    global is_bot_active
    if is_bot_active:
        bot.reply_to(message, 'Бот завершил свою работу. До свидания!')
        is_bot_active = False
    else:
        bot.reply_to(message, 'Бот не активен. Введи /start для начала.')


@bot.message_handler(commands=['help', 'about'])
def help_command(message):
    bot.reply_to(message, 'Раздел помощи. Информация о боте')

@bot.message_handler(commands=['search'])
def search_command(message):
    if is_bot_active:
        bot.reply_to(message, 'Какую песню хочешь скачать?')
    else:
        bot.reply_to(message, 'Для начала работы с ботом введите /start')

def send_message_safe(chat_id, text):
    """Функция для безопасной отправки длинных сообщений."""
    max_length = 4096  # Лимит Telegram
    for i in range(0, len(text), max_length):
        bot.send_message(chat_id, text[i:i + max_length])

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if is_bot_active:
        song_name = message.text.strip()
        
        results = search_song(song_name)
        
        if results:
            limited_results = results[:5]
            response = "Вот что я нашел:\n\n" + "\n".join(limited_results)
        else:
            response = "К сожалению, я не смог найти эту песню."
        
        send_message_safe(message.chat.id, response)
        
    else:
        bot.reply_to(message, 'Для начала работы с ботом введите /start')
    
    
def run_bot():
    """Запускает Telegram-бота"""
    bot.polling(none_stop=True)

if __name__ == "__main__":
    run_bot()
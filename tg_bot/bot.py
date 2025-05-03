from dotenv import load_dotenv
import django
import os
import telebot
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Запуск скрипта бота")

# Добавляем корневую директорию проекта в sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
logger.info(f"Добавлен путь в sys.path: {BASE_DIR}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_searcher.settings')
logger.info("Установлен DJANGO_SETTINGS_MODULE")

logger.info("Инициализация Django")
django.setup()
logger.info("Django успешно инициализирован")

from searcher.views import search_song
logger.info("Импортирована функция search_song")

load_dotenv()
logger.info("Загружены переменные окружения")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в .env")
    sys.exit(1)
logger.info("Получен TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
logger.info("Бот успешно создан")

# Флаг для отслеживания состояния работы бота
is_bot_active = False

@bot.message_handler(commands=['start'])
def start_command(message):
    global is_bot_active
    if not is_bot_active:
        bot.reply_to(message, 'Привет! Я твой бот по поиску музыки. Чтобы начать поиск, введи /search.\nЧтобы узнать, что умеет бот, введи /help или /about')
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
    bot.reply_to(message, 'Я бот для поиска музыки. Используй:\n/search <название песни> — найти песню\n/start — запустить бота\n/stop — остановить бота')

@bot.message_handler(commands=['search'])
def search_command(message):
    if is_bot_active:
        bot.reply_to(message, 'Какую песню хочешь скачать?')
    else:
        bot.reply_to(message, 'Для начала работы с ботом введи /start')

def send_message_safe(chat_id, text, parse_mode=None):
    """Отправляет сообщение, не превышая лимит Telegram."""
    max_length = 4096  # Лимит Telegram
    if len(text) <= max_length:
        try:
            bot.send_message(chat_id, text, parse_mode=parse_mode, disable_web_page_preview=True)
            logger.info(f"Отправлено сообщение: {text[:100]}...")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
    else:

        lines = text.split('\n')
        current_message = ""
        for line in lines:
            if len(current_message) + len(line) + 1 <= max_length:
                current_message += line + '\n'
            else:
                if current_message:
                    try:
                        bot.send_message(chat_id, current_message, parse_mode=parse_mode, disable_web_page_preview=True)
                        logger.info(f"Отправлена часть сообщения: {current_message[:100]}...")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке части сообщения: {e}")
                current_message = line + '\n'
        if current_message:
            try:
                bot.send_message(chat_id, current_message, parse_mode=parse_mode, disable_web_page_preview=True)
                logger.info(f"Отправлена последняя часть сообщения: {current_message[:100]}...")
            except Exception as e:
                logger.error(f"Ошибка при отправке последней части сообщения: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if is_bot_active:
        song_name = message.text.strip()
        logger.info(f"Получен запрос на поиск песни: {song_name}")
        bot.send_message(message.chat.id, 'Обрабатываю ваш запрос, пожалуйста, подождите', disable_web_page_preview=True)
        
        results = search_song(song_name)
        
        if results:
            response = "Вот что я нашел:\n\n"
            for idx, (link, file_size) in enumerate(results[:5], 1):
                size_mb = file_size / 1024 / 1024 if file_size != float('inf') else "неизвестно"
                size_str = f"{size_mb:.1f} MB" if isinstance(size_mb, float) else size_mb
                response += f"{idx}. <a href='{link}'>ссылка ({size_str})</a>\n"
                logger.info(f"Добавлена ссылка {idx}: {link[:100]}... (Размер: {size_str})")
            send_message_safe(message.chat.id, response, parse_mode='HTML')
        
            response = "\n<b>Как скачать песню:</b>\n"
            response += "- Для скачивания придется использовать VPN сервисы\n"
            response += "- На ПК: Щёлкните ссылку, нажмите Ctrl+S или правой кнопкой → \"Сохранить как...\" (.m4a).\n"
            response += "- На Android: Откройте ссылку в Chrome, нажмите ⋮ → \"Скачать\". Или используйте приложение \"Download Manager\" (Google Play).\n"
            response += "- На iPhone: Откройте в Safari, нажмите \"Поделиться\" → \"Сохранить в Файлы\". Или используйте \"Documents by Readdle\" (App Store).\n"
            response += "- Если не скачивается, попробуйте другую ссылку или повторите поиск."
            
            send_message_safe(message.chat.id, response, parse_mode='HTML')
        else:
            response = "К сожалению, я не смог найти эту песню."
            send_message_safe(message.chat.id, response, parse_mode='HTML')
        
    else:
        bot.reply_to(message, 'Для начала работы с ботом введи /start')

def run_bot():
    """Запускает Telegram-бота"""
    logger.info("Запуск polling")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Ошибка в polling: {e}")
        raise

if __name__ == "__main__":
    logger.info("Старт программы")
    run_bot()
from dotenv import load_dotenv
import django
import os
import telebot
import sys
import logging
from telebot import types 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Запуск скрипта бота")

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

is_bot_active = False
user_progress = {}

def create_main_keyboard():
    """Создает улучшенную клавиатуру"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('🎵 Найти музыку'),
        types.KeyboardButton('❓ Помощь'),
        types.KeyboardButton('🚫 Остановить')
    )
    return markup

def show_welcome(message):
    welcome = """
🎉 <b>Добро пожаловать в MelodyQuest!</b> 🎉

Я помогу вам найти и скачать любую музыку. Просто введите название трека или воспользуйтесь кнопками ниже.

<b>Основные команды:</b>
🎵 Найти музыку - поиск по названию
❓ Помощь - как пользоваться ботом
🚫 Остановить - выключить бота

Начните с кнопки <b>"🎵 Найти музыку"</b> или введите название трека!
"""
    bot.send_message(
        message.chat.id,
        welcome,
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(commands=['start'])
def start_command(message):
    global is_bot_active
    if not is_bot_active:
        show_welcome(message)
        is_bot_active = True
    else:
        bot.reply_to(message, '✅ Бот уже активен. Используйте кнопки меню!')

@bot.message_handler(commands=['stop'])
def stop_command(message):
    global is_bot_active
    if is_bot_active:
        remove_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Бот завершил свою работу. До свидания!', reply_markup=remove_keyboard)
        is_bot_active = False
    else:
        bot.reply_to(message, 'Бот не активен. Введи /start для начала.')

@bot.message_handler(commands=['help', 'about'])
@bot.message_handler(func=lambda message: message.text in ['❓ Помощь', 'Помощь'])
def help_command(message):
    help_text = """
<b>🎧 Как пользоваться ботом:</b>

1. Нажмите <b>"🎵 Найти музыку"</b> или введите /search
2. Введите название трека или исполнителя
3. Выберите подходящий вариант из результатов
4. Скачайте музыку по предоставленной ссылке

<b>🔍 Возможности:</b>
- Поиск по названию и исполнителю
- Быстрое скачивание

<b>📌 Полезные советы:</b>
- Используйте точные названия для лучшего результата
- Если трек не найден, попробуйте изменить запрос
"""
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='HTML',
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(commands=['stop'])
@bot.message_handler(func=lambda message: message.text in ['🚫 Остановить', 'Остановить'])
def stop_command(message):
    global is_bot_active
    if is_bot_active:
        bot.send_message(
            message.chat.id,
            '🛑 Бот остановлен. Для возобновления работы введите /start',
            reply_markup=types.ReplyKeyboardRemove()
        )
        is_bot_active = False
    else:
        bot.reply_to(message, 'ℹ️ Бот уже остановлен. Введите /start для запуска.')

@bot.message_handler(commands=['search'])
@bot.message_handler(func=lambda message: message.text in ['🎵 Найти музыку', 'Найти музыку'])
def search_command(message):
    if is_bot_active:
        msg = bot.send_message(
            message.chat.id,
            '🔍 Введите название трека или исполнителя:',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_search_query)
    else:
        bot.reply_to(message, '⚠️ Бот не активен. Введите /start для запуска.')

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


def process_search_query(message):
    song_name = message.text.strip()
    logger.info(f"Получен запрос на поиск песни: {song_name}")
    bot.send_message(message.chat.id, 'Обрабатываю ваш запрос, пожалуйста, подождите...')
    
    results = search_song(song_name)
    
    if results:
        response = "🎶 <b>Результаты поиска:</b>\n\n"
        for idx, (link, file_size) in enumerate(results[:5], 1):
            size_mb = file_size / 1024 / 1024 if file_size != float('inf') else "?"
            size_str = f"{size_mb:.1f}MB" if isinstance(size_mb, float) else f"{size_mb}MB"
            
            response = (
                f"{idx}. <b>Скачать</b> [{size_str}]:\n"
                f"   🔊 <a href='{link}'>Открыть в браузере</a>\n"
            )

            send_message_safe(
                message.chat.id,
                response,
                parse_mode='HTML',
            )
        
        # Добавляем инструкцию
        response = """
📥 <b>Как скачать музыку:</b>

<u>На компьютере:</u>
1. Кликните по ссылке "Скачать"
2. Нажмите <i>Ctrl+S</i> (Windows/Linux) или <i>Cmd+S</i> (Mac)
3. Выберите папку для сохранения

<u>На смартфоне:</u>
📱 <b>Android:</b>
• Используйте браузер Chrome
• Нажмите "⋮" → "Скачать"

🍏 <b>iPhone:</b>
• Откройте в Safari
• Нажмите "Поделиться" → "Сохранить в Файлы"

🔧 <i>Если не получается скачать, попробуйте другую ссылку или повторите поиск.</i>
"""

        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=create_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "😔 Не удалось найти трек. Попробуйте изменить запрос.",
            reply_markup=create_main_keyboard()
        )


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
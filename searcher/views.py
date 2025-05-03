import requests
import os
from dotenv import load_dotenv
import yt_dlp
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def search_song_youtube(song_name):
    api_key = os.getenv("YOUTUBE_API_KEY")
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": song_name,
        "type": "video",
        "key": api_key,
        "maxResults": 10
    }
    try:
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            return [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
        else:
            logger.error(f"Ошибка YouTube API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Ошибка при поиске на YouTube: {e}")
        return []

def get_download_link_yt_dlp(video_url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[acodec=aac]/bestaudio[acodec=opus][ext=webm][protocol!=hls][protocol!=m3u8]',
        'quiet': True,
        'noplaylist': True,
        'extractaudio': True,
        'geturl': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'audio/mp4,audio/webm,*/*;q=0.9',
        },
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            logger.info(f"Доступные форматы: {[f.get('ext') + ':' + f.get('protocol', 'unknown') + ':' + f.get('acodec', 'unknown') for f in formats]}")
            
            download_url = info.get('url') or info.get('direct_link')
            file_size = info.get('filesize', float('inf'))
            format_ext = info.get('ext', 'unknown')
            protocol = info.get('protocol', 'unknown')
            acodec = info.get('acodec', 'unknown')
            
            if not download_url:
                logger.error("Ссылка на скачивание не найдена")
                return None, None
            
            if protocol in ('hls', 'm3u8'):
                logger.error(f"Получен потоковый формат (protocol={protocol}, ext={format_ext}, acodec={acodec}): {download_url[:100]}...")
                return None, None
            
            # Проверяем заголовки ответа
            try:
                response = requests.head(download_url, allow_redirects=True)
                headers = response.headers
                logger.info(f"Заголовки ответа: Content-Type={headers.get('Content-Type', 'unknown')}, Content-Disposition={headers.get('Content-Disposition', 'none')}")
            except Exception as e:
                logger.error(f"Ошибка проверки заголовков: {e}")
            
            logger.info(f"Получена ссылка: {download_url[:100]}... (Формат: {format_ext}, Протокол: {protocol}, Кодек: {acodec}, Размер: {file_size})")
            return download_url, file_size
        except Exception as e:
            logger.error(f"Ошибка при получении ссылки: {e}")
            return None, None

def search_song(song_name):
    video_links = search_song_youtube(song_name)
    results = []
    
    for link in video_links:
        download_url, file_size = get_download_link_yt_dlp(link)
        if download_url:
            results.append((download_url, file_size))
        time.sleep(0.5)  # Задержка для избежания ограничений
    
    return results[:10]  # Возвращаем до 10 кортежей (url, size)